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
    Members, Guilds, Clans,
    TransactionMain
)


class Rating(BasicCog, name='rating'):
    
    limit: int = 50
    limit_minutes_time: int = 1440

    def __init__(self: "BasicCog", bot: commands.Bot) -> None:
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
                member.daily_exp_msg_limit_time = str(self.limit_minutes_time)
                orm.commit()

            for member in Members.select(lambda m: int(m.daily_exp_msg_limit_time) > 0):
                member.daily_exp_msg_limit_time = str(int(member.daily_exp_msg_limit_time) - 1)
                orm.commit()

        t = datetime.now()
        if '%s:%s' % (t.hour, t.minute) == '15:5':
            await self._log('start daily drop clans')
            await self.bot.get_cog('clans').reward_top_clans()

    @check_daily_exp_limit.before_loop
    async def before_check_daily_exp_limit(self: "Rating") -> None:
        """
        Start updates to the daily exp limit time indicator, counts the time until the cooldown is completed
        """
        await self.bot.wait_until_ready()

    async def check_rank_lvl(
        self: "Rating", id: int, user_info: bool = False
    ) -> ty.Union[ty.Tuple[bool, int, int], ty.Tuple[bool, int], int]:
        """
        Calculation of the necessary amount of experience to increase the level of the user
        """
        with orm.db_session:
            user: Members = Members.get(id=str(id))

            def_exp: int = 75
            count_lvl: int = 1
            count: int = 5
            coefficient: int = 2

            while count_lvl != int(user.lvl_rank):
                if count_lvl >= count:
                    continue

                count_lvl += 1

                if count_lvl != count:
                    def_exp = ceil(def_exp * coefficient)
                    continue

                if count == 5:
                    coefficient -= 0.2

                elif count == 10:
                    coefficient -= 0.3

                elif coefficient != 1.1:
                    coefficient -= 0.1

                coefficient = float_round(coefficient, 1)
                def_exp = ceil(def_exp * coefficient)
                count += 5

            if int(user.exp_rank) >= int(def_exp):
                await self._log(
                    f'check rank lvl: {user.id}, {user.name}\n'
                    f'coefficient: {coefficient}, def_exp: {def_exp}\n'
                    f'status: T, lvl up'
                )

                if not user_info:
                    return True, def_exp * 0.1, int(user.exp_rank) - int(def_exp)
                return int(def_exp)

            await self._log(
                f'check rank lvl: user.id, user.name\n'
                f'coefficient: {coefficient}, def_exp: {def_exp}\n'
                f'status: F, lvl not up'
            )

            if not user_info:
                return False, None, None
            return int(def_exp)

    async def new_lvl(self: "Rating", id: int, send_msg: bool = True) -> None:
        """
        User Level increase
        """
        check, token, free_exp = await self.check_rank_lvl(id)

        if not check:
            return None

        with orm.db_session:
            user: Members = Members.get(id=str(id))
            user.exp_rank = "0" if free_exp is None else str(free_exp)
            user.exp_all = str(int(user.exp_all) + free_exp)
            user.lvl_rank = str(int(user.lvl_rank) + 1)
            user.tokens = str(float(user.tokens) + float(token))

        await send_log_channel(
            title='Level up',
            text=f'Member: {self.bot.get_user(int(user.id)).mention}\nNew lvl: '
                 f'`{user.lvl_rank}`\nECT: `{str(token)}`',
            bot=self.bot
        )

        if send_msg:
            await send_embed(
                title='Level up',
                text=f'Your new lvl is {user.lvl_rank}',
                color=GREEN_COLOR,
                member=self.bot.get_user(int(user.id))
            )

        with orm.db_session:
            TransactionMain(
                type='lvl_up',
                date=datetime.now(),
                user_id=user.id,
                get_tokens=str(token),
                new_lvl=user.lvl_rank
            )

        await self._log(
            'lvl up:', user.id, user.name, 
            'lvl up to', user.lvl_rank, ' token give:',
            ' ', str(round(token))
        )
        await self.new_lvl(id)

    async def check_members_guild(self: "Rating", guild: discord.Guild) -> None:
        """
        Checking server users for availability in the database/checking awards
        """
        await self._log(f"check members guild: {guild.id} {guild.name}")

        with orm.db_session:
            m_guild: Guilds = Guilds.get(id=str(guild.id))

        if m_guild.frozen:
            return None

        for member in guild.members:
            if member.bot:
                continue
            
            if guild.id == discord_config['server_main']:
                if Members.get(id=str(member.id)) is None:
                    await add_user_to_database(member)
                    await asyncio.sleep(0.5)
                    continue

                await self.check_status(member)
                await asyncio.sleep(0.5)
                continue

            if Members.get(id=str(member.id)) is not None:
                await self.check_status(member)

    async def check_status(self: "Rating", member: Member) -> None:
        """
        Checking all kinds of user awards
        """
        guild: Guild = member.guild

        with orm.db_session:
            user = Members.get(id=str(member.id))
            m_guild: Guilds = Guilds.get(id=str(member.guild.id))

        if not user.ether_status or \
            not user.nods_status:
            return None

        if m_guild.role_ether is None or \
            m_guild.role_nods is None:
                return None

        if guild.get_role(int(m_guild.role_ether)) is None or \
            guild.get_role(int(m_guild.role_nods)) is None:
                return None

        with contextlib.suppress(Exception):
            await member.add_roles(
                guild.get_role(int(m_guild.role_ether))
            )
            await asyncio.sleep(0.1)
            
            await member.add_roles(
                guild.get_role(int(m_guild.role_nods))
            )

            await self._log(
                f"role_ether get: {member.id}, {member.name}\n"
                f'guild: {guild.id}, {guild.name}'
            )

            await self._log(
                f"role_nods get: {member.id}, {member.name}\n"
                f'guild: {guild.id}, {guild.name}'
            )


def setup(bot):
    bot.add_cog(Rating(bot))
    print(f'=== cogs {Rating.__name__} loaded ===')
