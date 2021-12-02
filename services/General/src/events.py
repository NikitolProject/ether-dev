import asyncio

import contextlib

import discord

from discord_components import DiscordComponents
from discord.ext import commands

from . import BasicCog, discord_config
from .utils import *
from .database import (
    Clans, Guilds, Members,
    RatingClans
)


class Events(BasicCog, name="events"):

    @commands.Cog.listener()
    async def on_ready(self: "Events") -> None:
        """
        The main event that displays the bot's readiness to work
        """
        DiscordComponents(self.bot)
        await self._log(f'Discord bot "{self.bot.user.name}" connected')

        with orm.db_session:
            for guild in self.bot.guilds:
                if await white_list_guild_owners(guild) and Guilds.select().exists() and \
                    Guilds.get(id=str(guild.id)) is None or guild.id == discord_config["server_main"]:
                    if guild.id != discord_config['server_main']:
                        await add_guild_to_database(guild)
                        await create_category_guild(guild)
                        continue
                    
                    if Guilds.get(id=str(guild.id)) is None:
                        await add_to_database_main_guild(guild)

                        if discord_config['create_msg_rating_wallet']:
                            await create_main_server_rating_wallet(guild)

        await self._log(f'Discord bot "{self.bot.user.name}" ready')

    @commands.Cog.listener()
    async def on_guild_join(self: "Events", guild: discord.Guild) -> None:
        """
        An event for processing a user who has connected to the system
        """
        await self._log(f'New guild "{guild}" joined')
        
        if not await white_list_guild_owners(guild):
            return None

        with orm.db_session:
            if Guilds.select().exists() and Guilds.get(id=str(guild.id)) is None:
                if guild.id != discord_config['server_main']:
                    await add_guild_to_database(guild)
                    await create_category_guild(guild)
                    return None

                await add_to_database_main_guild(guild)
                return None

            elif Guilds.get(id=str(guild.id)).forzen:
                await self.__defrost_guild(guild)
    
    @commands.Cog.listener()
    async def on_guild_remove(self: "Events", guild: discord.Guild) -> None:
        """
        Event for processing a server that has disconnected from the system
        """
        await self._log(f'Guild "{guild}" left')

        with orm.db_session:
            if Guilds.select().exists() and Guilds.get(id=str(guild.id)) is not None:
                await self.__frozen_guild(guild)

    async def __frozen_guild(self: "Events", guild: discord.Guild) -> None:
        """
        Freezing the server and the clans that are in it
        """
        with orm.db_session:
            m_guild: Guilds = Guilds.get(id=str(guild.id))
            m_guild.forzen = True

            await self._log(
                'guild is frozen:', guild.id,
                guild.name, 'owner:', guild.owner_id, 
                guild.owner.name
            )
            with contextlib.suppress(Exception):
                for clan in m_guild.clans.split(","):
                    clan: Clans = Clans.get(_id=int(clan))
                    clan.forzen = True

                    await self._log(
                        'clan is frozen:', clan.token, 
                        'owner:', clan.owner_clan
                    )

                    RatingClans.get(clan_id=str(clan._id)).delete()

                TransactionMain(
                    type='frost_guild',
                    date=datetime.now(),
                    guild_id=str(guild.id),
                    owner=str(guild.owner_id),
                    clans=m_guild.clans
                )

    async def __defrost_guild(self: "Events", guild: discord.Guild) -> None:
        """
        Defrosting the server and the clans in it
        """
        await self._log(
            f'Guild "{guild}" defrosted'
        )

        with orm.db_session:
            m_guild = Guilds.get(id=str(guild.id))

        if m_guild is None or not m_guild.frozen or \
            not guild.self_role.permissions.administrator:
            return None

        try:
            await self.__check_system_category(guild, m_guild)
        except Exception as e:
            await self._error(
                'check_system_category_error:', e, 
                'guild:', guild.id, guild.name
            )

        try:
            await self.__defrost_guild_in_database(guild)
        except Exception as e:
            await self._error(
                'defrost error:', e, 'guild:', 
                guild.id, guild.name
            )
        
    async def __defrost_guild_in_database(self: "Events", guild: discord.Guild) -> None:
        with orm.db_session:
            m_guild = Guilds.get(id=str(guild.id))
            m_guild.forzen = False

            await self._log(
                'guild is defrost:', guild.id, guild.name, 
                'owner:', guild.owner_id, guild.owner.name
            )

            for clan in m_guild.clans.split(','):
                with contextlib.suppress(Exception):
                    clan = Clans.get(_id=int(clan))
                    clan.forzen = False

                    await self._log(
                        'clan is defrost:', clan.token, 
                        'owner:', clan.owner_clan
                    )
            TransactionMain(
                type='defrost_guild',
                date=datetime.now(),
                guild=str(guild.id),
                owner=str(guild.owner_id),
                clans=m_guild.clans
            )

    async def __check_system_category(
        self: "Events", guild: discord.Guild, m_guild: Guilds
    ) -> None:
        guild_channels = (
            int(m_guild.system_ch_category), 
            int(m_guild.system_ch_city_setup),
            int(m_guild.system_ch_help)
        )
        for channel in guild_channels:
            if guild.get_channel(channel) is None:
                await self.__delete_category(guild, guild_channels)
                await create_category_guild(guild)
                break
    
    async def __delete_category(
        self: "Events", guild: discord.Guild, _guild_channels: dict
    ) -> None:
        for channel in _guild_channels.items():
            with contextlib.suppress(Exception):
                await guild.get_channel(channel).delete()
        
        with orm.db_session:
            m_guild = Guilds.get(id=str(guild.id))
            m_guild.system_ch_category = None
            m_guild.system_ch_city_setup = None
            m_guild.system_ch_help = None
            m_guild.system_ch_city_setup_msg = None


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Events(bot))
    print(f'=== cogs {Events.__name__} loaded ===')
