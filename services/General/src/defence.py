import datetime

import typing as ty

import discord

from discord import Guild, Role, TextChannel, VoiceChannel
from discord.channel import CategoryChannel
from discord.ext import commands, tasks

from . import *
from .utils import *
from .utils.messages import *
from .database import *


class Defence(BasicCog, name='defence'):

    bans: dict = {}

    async def __delete_category(
        self: "Defence", guild: Guild, _guild_channels: dict
    ) -> None:
        for _, v in _guild_channels.items():
            with contextlib.suppress(Exception):
                await guild.get_channel(v).delete()

        with orm.db_session(optimistic=False):
            m_guild: Guilds = Guilds.get(id=str(guild.id))
            m_guild.system_ch_category = None
            m_guild.system_ch_city_setup = None
            m_guild.system_ch_help = None
            m_guild.system_ch_city_setup_msg = None

    async def __check_system_category(self: "Defence", guild: Guild, m_guild: Guilds) -> None:
        guild_channels = {
            "system_ch_category": int(m_guild.system_ch_category),
            "system_ch_city_setup": int(m_guild.system_ch_city_setup),
            "system_ch_help": int(m_guild.system_ch_help),
        }

        for _, v in guild_channels.items():
            if guild.get_channel(v) is None:
                await self.__delete_category(guild, guild_channels)
                await create_category_guild(guild)
                break

    async def defrost_guild(self: "Defence", guild: Guild, interaction: Interaction) -> None:
        """
        Defreezing the server and the clans that are in it
        """
        await self._log(
            "Defreezing the server and the clans that are in it"
        )

        with orm.db_session:
            m_guild: Guilds = Guilds.get(id=str(guild.id))
            if m_guild is None and m_guild.frozen or not guild.self_role.permissions.administrator:
                await interaction.respond(
                    title="You can't unfreeze the city",
                    description="Since your city is not frozen, either the bot does not have sufficient privileges",
                    color=discord.Color.red()
                )
                return None

            try:
                await self.__check_system_category(guild, m_guild)

            except Exception as e:
                await self._error('check_system_category_error:', e, 'guild:', guild.id, guild.name)

            try:
                m_guild.frozen = False
                await self._log(
                    'guild is defrost:', guild.id, guild.name, 
                    'owner:', guild.owner_id, guild.owner.name
                )
                guild_clans: list = m_guild.clans

                for clan in guild_clans:
                    clan: Clans = Clans.get(_id=int(clan))
                    clan.frozen = False
                    await self._log(
                        'clan is defrost:', clan.token, 
                        'owner:', clan.owner_clan
                    )

                TransactionMain(
                    type="defrost_guild",
                    date=datetime.now(),
                    guild=str(guild.id),
                    owner=str(guild.owner_id),
                    clans=guild_clans
                )

                await interaction.author.send(
                    embed=discord.Embed(
                        title=f"{guild.name} is defrosted",
                        color=discord.Color.green()
                    )
                )

            except Exception as e:
                await self._error(
                    'defrost error:', e, 'guild:', 
                    guild.id, guild.name
                )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Defence(bot))
    print(f'=== cogs {Defence.__name__} loaded ===')
