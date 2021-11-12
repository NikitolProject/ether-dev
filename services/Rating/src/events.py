import asyncio
import contextlib

import discord

import typing as ty

import pony.orm as orm

from math import ceil
from random import randint
from datetime import datetime

from discord.ext import commands, tasks

from . import *
from .utils import *
from .database import (
    Members, Guilds, Clans
)


class Rating(BasicCog, name='rating'):
    
    limit: int = 50
    limit_minutes_time: int = 1440

    def __init__(self: "Rating", bot: commands.Bot) -> None:
        super().__init__(bot)
        self.check_daily_exp_limit.start()

    @tasks.loop(minutes=1)
    async def check_daily_exp_limit(self: "Rating") -> None:
        """
        Updates to the daily exp limit time indicator, counts the time until the cooldown is completed
        """
        with orm.db_session:
            for member in Members.select(lambda m: int(m.daily_exp_msg_limit_time) == 0):
                member.daily_exp_msg_limit = str(self.limit)

            for member in Members.select(lambda m: int(m.daily_exp_msg_limit_time) > 0):
                member.daily_exp_msg_limit_time = str(int(member.daily_exp_msg_limit_time) - 1)

        t = datetime.now()
        if '%s:%s' % (t.hour, t.minute) == '15:5':
            await self._log('start daily drop clans')
            await self.bot.get_cog('clans').reward_top_clans()

    @check_daily_exp_limit.before_loop
    async def before_check_daily_exp_limit(self: "Rating") -> None:
        """
        Initializing the event check_daily_exp_limit
        """
        await self._log('start check daily exp limit')
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self: "Rating", message: discord.Message) -> None:
        """
        Event receiving messages from users, accrues experience
        """
        await self._log('start event receiving messages from users, accrues experience')

        if message.channel.type == discord.ChannelType.private:
            return None

        if message.author.bot or randint(30, 50) < len(message.content) < randint(60, 100):
            return None

        with orm.db_session:
            user = Members.get(id=str(message.author.id))

        if user is None or int(user.daily_exp_msg_limit) > 0:
            return None
        
        exp_rank = await self.__check_return_exp(message, int(user.id))

        if exp_rank is None:
            return None
        
        with orm.db_session:
            user: Members = Members.get(id=str(message.author.id))
            user.exp_rank = str(int(user.exp_rank) + exp_rank)
            user.daily_exp_msg_limit = str(int(user.daily_exp_msg_limit) - 1)

            if int(user.daily_exp_msg_limit_time) <= 0:
                user.daily_exp_msg_limit_time = str(int(user.daily_exp_msg_limit_time) + self.limit_minutes_time)

        await self.__new_lvl(user._id)

    async def __check_return_exp(
        self: "Rating", ctx: commands.Context, _id: int
    ) -> ty.Union[int, None]:
        """
        The function that checks the channels returns the amount of experience
        """
        with orm.db_session:
            guild: Guilds = Guilds.get(id=str(ctx.guild.id))
            category: Clans = Clans.get(category_id=str(ctx.channel.category.id))

        if guild.frozen:
            return None
    
        if ctx.guild.id == discord_config['server_main'] and \
            ctx.channel.id == ether_city_channels['vi1-everyone']:
            return 10

        with contextlib.suppress(Exception):
            if category is not None and _id == int(category.owner_clan) or \
                 _id in category.nods.split(',') and \
                      ctx.channel.id == category.channel_engage_id:
                        return 10


def setup(bot):
    bot.add_cog(Rating(bot))
    print(f'=== cogs {Rating.__name__} loaded ===')