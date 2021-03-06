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
    Members, Guilds,
    TransactionMain
)


class Rating(BasicCog, name='rating'):
    
    limit: int = 50
    limit_minutes_time: int = 1440

    async def __check_rank_lvl(
        self: "Rating", _id: int, user_info: bool = False
    ) -> ty.Union[ty.Tuple[bool, int, int], ty.Tuple[bool, int], int]:
        """
        Calculation of the necessary amount of experience to increase the level of the user
        """
        with orm.db_session(optimistic=False):
            user: Members = Members.get(_id=_id)

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
                'check rank lvl:', user.id, user.name,
                'coefficient', coefficient, 'def_exp:', def_exp, 
                'status:', 'T, lvl up'
            )

            if not user_info:
                return True, def_exp * 0.1, int(user.exp_rank) - int(def_exp)
            return int(def_exp)

        await self._log(
            'check rank lvl:', user.id, user.name, 
            'coefficient', coefficient, 'def_exp:', def_exp, 
            'status:', 'F, lvl not up'
        )

        if not user_info:
            return False, None, None
        return int(def_exp)

    async def __new_lvl(self: "Rating", _id: int, send_msg: bool = True) -> None:
        """
        User Level increase
        """
        check, token, free_exp = await self.__check_rank_lvl(_id)

        if not check:
            return None

        with orm.db_session(optimistic=False):
            user: Members = Members.get(_id=_id)
            user.exp_rank = 0 if free_exp is None else free_exp
            user.exp_all = str(int(user.exp_all) - free_exp)
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

        with orm.db_session(optimistic=False):
            TransactionMain(
                type='lvl_up',
                date=datetime.now(),
                user_id=user.id,
                get_tokens=token,
                new_lvl=user.lvl_rank
            )

        await self._log(
            'lvl up: ', user.id, user.name, 
            'lvl up to', user.lvl_rank, ', token give:', 
            str(round(token))
        )
        await self.__new_lvl(_id)

    async def check_members_guild(self: "Rating", guild: discord.Guild) -> None:
        """
        Checking server users for availability in the database/checking awards
        """
        await self._log('check members guild:', guild.id, guild.name)

        with orm.db_session(optimistic=False):
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

                    await self.__check_status(member)
                    await asyncio.sleep(0.5)
                    continue

                if Members.get(id=str(member.id)) is not None:
                    await self.__check_status(member)

    async def __check_status(self: "Rating", member: Member) -> None:
        """
        Checking all kinds of user awards
        """
        guild: Guild = member.guild

        with orm.db_session(optimistic=False):
            user = Members.get(id=str(member.id))
            m_guild: Guilds = Guilds.get(id=str(member.guild.id))

        if not user.ether_status and \
            not user.nods_status:
            return None

        if m_guild.role_ether is None and \
            m_guild.role_nods is None:
                return None

        if m_guild.role_ether == '' and \
            m_guild.role_nods == '':
                return None

        if guild.get_role(int(m_guild.role_ether)) is None and \
            guild.get_role(int(m_guild.role_nods)) is None:
                return None

        if user.ether_status and guild.get_role(int(m_guild.role_ether)) not in member.roles:
            await member.add_roles(
                guild.get_role(int(m_guild.role_ether))
            )
            await asyncio.sleep(0.1)

            await self._log(
                "role_ether", 'get: ', member.id, member.name, 
                'guild: ', guild.id, guild.name
            )

        if user.nods_status and guild.get_role(int(m_guild.role_nods)) not in member.roles:
            await member.add_roles(
                guild.get_role(int(m_guild.role_nods))
            )

            await self._log(
                "role_nods", 'get: ', member.id, member.name, 
                'guild: ', guild.id, guild.name
            )


def setup(bot):
    bot.add_cog(Rating(bot))
    print(f'=== cogs {Rating.__name__} loaded ===')
