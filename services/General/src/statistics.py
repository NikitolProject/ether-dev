import asyncio

import discord

import pony.orm as orm

from discord.ext import commands

from . import *
from .utils import *
from .database import Guilds, Members, Clans


class Statistics(BasicCog, name='statistics'):

    members_count: set = set()

    def _remembers_count(self: "Statistics") -> int:
        """
        Counting the total number of DC
        """
        self.members_count = set()
        with orm.db_session:
            for guild in Guilds.select(lambda g: not g.frozen):
                if not guild.main_server and not guild.verification:
                    continue

                guild = self.bot.get_guild(int(guild.id))
                if guild is None:
                    continue

                self.__get_members_from_guild(guild)

        return len(self.members_count)

    def __get_members_from_guild(self: "Statistics", guild: discord.Guild) -> list:
        """
        Getting a list of guild members
        """
        with orm.db_session:
            for member in guild.members:
                if member.bot:
                    continue

                user = Members.get(id=str(member.id))
                if user is not None and user.vi1_status:
                    self.members_count.add(member.id)

    async def statistics(cls: "Statistics") -> None:
        """
        Displays statistics on the main server of ether city
        """
        await cls._log(f'{cls.__class__.__name__} is running')

        member_count = cls._remembers_count()

        with orm.db_session:
            clan_count = Clans.select().count() if Clans.select().exists() else 0
        
            ect = sum(
                float(member.tokens) for member in Members.select()
            )

            ect += sum(
                int(clan.vault1) for clan in Clans.select()
            )

            ect += sum(
                sum(
                    int(val[1]) for val in cls.__get_valut0(clan.vault0)
                ) for clan in Clans.select()
            )

        await cls.bot.get_channel(
            ether_city_channels['st_member_count']
        ).edit(
            name=f'* DCs: {member_count}'
        )

        await cls.bot.get_channel(
            ether_city_channels['st_ect_count']
        ).edit(
            name=f'* ECT: {float_round(ect, 1)}'
        )

        await cls.bot.get_channel(
            ether_city_channels['st_clan_count']
        ).edit(
            name=f'* Cities: {clan_count}'
        )

        await cls._log(f'statistics dc: {member_count}')
        await cls._log(f'statistics ect: {ect}')
        await cls._log(f'statistics cities: {clan_count}')

    @classmethod
    def __get_valut0(cls: "Statistics", valut0: list) -> list:
        return [i.split(":") for i in valut0]


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Statistics(bot))
    print(f'=== cogs {Statistics.__name__} loaded ===')
