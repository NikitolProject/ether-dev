import datetime

import typing as ty

import discord

from discord import Guild, Role, TextChannel
from discord.ext import commands

from . import *
from .utils import *
from .utils.messages import *
from .database import *


class Defence(BasicCog, name='defence'):

    bans: dict = {}

    def __init__(self: "Defence", bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self.func_system_list = {
            'system_ch_category': self.city_setup_category_re_create,
            'system_ch_city_setup': self.city_setup_re_create,
            'system_ch_help': self.help_re_create
        }
        self.func_clan_list = {
            'category_id': self.clan_category_re_create,
            'channel_join_id': self.join_re_create,
            'channel_engage_id': self.engage_re_create,
            'channel_marketplace_id': self.marketplace_re_create,
            'channel_wallet_id': self.wallet_re_create,
            'channel_statistics_id': self.statistics_re_create,
            'channel_logs_id': self.logs_re_create,
            'channel_help_id': self.c_help_re_create,
            'channel_voice_id': self.voice_re_create
        }

    async def check_bot_admin_perm(self: "Defence", guild: Guild) -> ty.Union[bool, None]:
        """
        Checking for administrator rights
        """
        bot_member = guild.get_member(self.bot.user.id)
        if bot_member.guild_permissions.administrator:
            return True

    @staticmethod
    async def new_role(role: Role) -> Role:
        """
        Recreating a deleted role
        """
        return await role.guild.create_role(
            name=role.name, permissions=role.permissions, 
            colour=role.colour, hoist=role.hoist, 
            mentionable=role.mentionable
        )

    @staticmethod
    async def new_channel(channel: discord.TextChannel) -> discord.TextChannel:
        """
        Re-creating a remote channel
        """
        return await channel.guild.create_text_channel(
            name=channel.name, overwrites=channel.overwrites, 
            category=channel.category, position=channel.position
        )

    async def role_system_re_create(
        self: "Defence", role: Role, 
        m_guild: Guilds, status: str
    ) -> None:
        """
        Re-creating the system role
        """
        with orm.db_session:
            new_role = await self.new_role(role)

            if status == 'role_ether':
                m_guild.role_ether = str(new_role.id)
            elif status == 'role_nods':
                m_guild.role_nods = str(new_role.id)
        await self.bot.get_cog('rating').check_members_guild(role.guild)

    async def role_clan_re_create(
        self: "Defence", role: Role, clan: Clans, status: str
    ) -> None:
        """
        Re-creating the system role
        """
        with orm.db_session:
            new_role = await self.new_role(role)

            if status == "role_owner_id":
                clan.role_owner_id = new_role.id
                await new_role.guild.get_member(int(clan.owner_clan)).add_roles(new_role)
            
            elif status == "role_support_id":
                clan.role_support_id = new_role.id
                for member in clan.supports:
                    with contextlib.suppress(Exception):
                        await new_role.guild.get_member(member).add_roles(new_role)

            elif status == "role_nods_id":
                clan.role_nods_id = new_role.id
                for member in clan.nods:
                    with contextlib.suppress(Exception):
                        await new_role.guild.get_member(member).add_roles(new_role)

            await self.__set_overwrites(clan, new_role, status)

    async def __set_overwrites(
        self: "Defence", clan: Clans, new_role: Role, _status: str
    ) -> None:
            channels = {
                'category_id': [clan.category_id, {
                    'role_owner_id': discord.PermissionOverwrite(read_messages=True, manage_roles=False, manage_messages=True),
                    'role_nods_id': discord.PermissionOverwrite(read_messages=True)
                }],
                'channel_join_id': [clan.channel_join_id, {
                    'role_owner_id': discord.PermissionOverwrite(read_messages=True, send_messages=True,
                                                                 manage_roles=False, manage_channels=False,
                                                                 manage_messages=True),
                    'role_nods_id': discord.PermissionOverwrite(read_messages=True, send_messages=False)
                }],
                'channel_engage_id': [clan.channel_engage_id, {
                    'role_owner_id': discord.PermissionOverwrite(read_messages=True, manage_roles=False,
                                                                 manage_messages=True),
                    'role_nods_id': discord.PermissionOverwrite(read_messages=True)
                }],
                'channel_marketplace_id': [clan.channel_marketplace_id, {
                    'role_owner_id': discord.PermissionOverwrite(read_messages=True, manage_roles=False, manage_messages=True),
                    'role_nods_id': discord.PermissionOverwrite(read_messages=True, send_messages=False)
                }],
                'channel_wallet_id': [clan.channel_wallet_id, {
                    'role_owner_id': discord.PermissionOverwrite(read_messages=True, manage_roles=False, manage_messages=True),
                    'role_nods_id': discord.PermissionOverwrite(read_messages=True, send_messages=False)
                }],
                'channel_statistics_id': [clan.channel_statistics_id, {
                    'role_owner_id': discord.PermissionOverwrite(read_messages=True, manage_roles=False, manage_messages=True),
                    'role_nods_id': discord.PermissionOverwrite(read_messages=True, send_messages=False)
                }],
                'channel_logs_id': [clan.channel_logs_id, {
                    'role_owner_id': discord.PermissionOverwrite(read_messages=True, manage_roles=False, manage_messages=True),
                    'role_nods_id': discord.PermissionOverwrite(read_messages=True, send_messages=False)
                }],
                'channel_help_id': [clan.channel_help_id, {
                    'role_owner_id': discord.PermissionOverwrite(read_messages=True, manage_roles=False, manage_messages=True),
                    'role_nods_id': discord.PermissionOverwrite(read_messages=True, send_messages=False)
                }],
                'channel_voice_id': [clan.channel_voice_id, {
                    'role_owner_id': discord.PermissionOverwrite(connect=True, manage_roles=True, manage_channels=False, manage_messages=True),
                    'role_nods_id': discord.PermissionOverwrite(connect=True)
                }],
            }
            guild: Guild = self.bot.get_guild(new_role.guild.id)
            for _, v in channels.items():
                try:
                    channel = guild.get_channel(int(v[0]))
                    await channel.set_permissions(new_role, overwrite=v[1][_status])

                except Exception as e:
                    await self._error(e)

    @classmethod
    async def clan_category_re_create(
        cls: "Defence", channel: TextChannel, clan: Clans
    ) -> None:
        """
        Re-creation of the clan category
        """
        new_category = await channel.guild.create_category(
            name=channel.name, overwrites=channel.overwrites
        )
        with orm.db_session:
            clan.category_id = str(new_category.id)

        await channel.guild.get_channel(
            clan.channel_join_id).edit(
            category=new_category
        )
        await channel.guild.get_channel(
            clan.channel_engage_id).edit(
            category=new_category
        )
        await channel.guild.get_channel(
            clan.channel_marketplace_id).edit(
            category=new_category
        )
        await channel.guild.get_channel(
            clan.channel_wallet_id).edit(
            category=new_category
        )
        await channel.guild.get_channel(
            clan.channel_statistics_id).edit(
            category=new_category
        )
        await channel.guild.get_channel(
            clan.channel_logs_id).edit(
            category=new_category
        )
        await channel.guild.get_channel(
            clan.channel_help_id).edit(
            category=new_category
        )
        await channel.guild.get_channel(
            clan.channel_voice_id).edit(
            category=new_category
        )

    @classmethod
    async def voice_re_create(
        cls: "Defence", channel: TextChannel, clan: Clans
    ) -> None:
        """
        Re-creating the voice channel
        """
        new_channel = await channel.guild.create_voice_channel(
            name=channel.name, overwrites=channel.overwrites, 
            category=channel.category, position=channel.position
        )
        with orm.db_session:
            clan.channel_voice_id = str(new_channel.id)

    async def c_help_re_create(
        self: "Defence", channel: TextChannel, clan: Clans
    ) -> None:
        """
        Re-creation of the clan <<help>> channel
        """
        new_channel = await self.new_channel(channel)
        channel_marketplace = self.bot.get_channel(clan.channel_marketplace_id)
        channel_wallet = self.bot.get_channel(int(clan.channel_wallet_id))
        channel_engage = self.bot.get_channel(int(clan.channel_engage_id))
        channel_join = self.bot.get_channel(int(clan.channel_join_id))
        channel_stats = self.bot.get_channel(int(clan.channel_statistics_id))

        await create_city_help_msg(
            new_channel, channel_marketplace, channel_wallet, 
            channel_engage, channel_join, channel_stats
        )

        with orm.db_session:
            clan.channel_help_id = str(new_channel.id)

    async def logs_re_create(
        self: "Defence", channel: TextChannel, clan: Clans
    ) -> None:
        """
        Re-creation of the clan <<logs>> channel
        """
        new_channel = await self.new_channel(channel)

        with orm.db_session:
            clan.channel_logs_id = str(new_channel.id)

    async def statistics_re_create(self: "Defence", channel: TextChannel, clan: Clans) -> None:
        """
        Re-creation of the clan <<statistics>> channel
        """
        new_channel = await self.new_channel(channel)

        with orm.db_session:
            rating: RatingClans = RatingClans.get(clan_id=clan._id)

            if rating is None:
                msg = await create_statistics_msg(new_channel, clan.total_exp)
            else:
                msg = await create_statistics_msg(new_channel, clan.total_exp, rating, clan)
                rating.channel_statistics_id = str(new_channel.id)
                rating.msg_statistics_id = str(msg.id)

    async def wallet_re_create(self: "Defence", channel: TextChannel, clan: Clans) -> None:
        """
        Re-creation of the clan <<wallet>> channel
        """
        new_channel = await self.new_channel(channel)
        msg = await create_wallet_msg(new_channel)

        with orm.db_session:
            clan.channel_wallet_id = str(new_channel.id)
            clan.msg_wallet_id = str(msg.id)

    async def marketplace_re_create(self, channel, clan):
        """
        Re-creation of the clan <<marketplace>> channel
        """
        new_channel = await self.new_channel(channel)
        msg = await create_marketplace_msg(new_channel)

        with orm.db_session:
            clan.channel_marketplace_id = str(new_channel.id)
            clan.msg_marketplace_id = str(msg.id)

    async def engage_re_create(self: "Defence", channel: TextChannel, clan: Clans) -> None:
        """
        Re-creation of the clan <<engage>> channel
        """
        new_channel = await self.new_channel(channel)

        with orm.db_session:
            clan.channel_engage_id = str(new_channel.id).id

    async def join_re_create(self: "Defence", channel: TextChannel, clan: Clans) -> None:
        """
        Re-creation of the clan <<join>> channel
        """
        new_channel = await self.new_channel(channel)
        msg = await create_join_msg(new_channel, clan.name)

        with orm.db_session:
            clan.channel_join_id = str(new_channel.id)
            clan.msg_join_id = str(msg.id)

    @classmethod
    async def city_setup_category_re_create(
        cls: "Defence", channel: TextChannel, m_guild: Guilds
    ) -> None:
        """
        Re-creation of the system category
        """
        new_category = await channel.guild.create_category(
            name=channel.name, overwrites=channel.overwrites
        )

        with orm.db_session:
            m_guild.system_ch_category = str(new_category.id)

        for ch in [m_guild.system_ch_city_setup, m_guild.system_ch_help]:
            try:
                await channel.guild.get_channel(ch).edit(category=new_category)

            except Exception as e:
                await cls._error(cls, e)

    async def city_setup_re_create(
        self: "Defence", channel: TextChannel, m_guild: Guilds
    ) -> None:
        """
        Re-creation of the system <<city-setup>> channel
        """
        new_channel = await self.new_channel(channel)
        msg = await create_city_setup_msg(
            new_channel, channel.guild.get_channel(
                m_guild.system_ch_help
            )
        )

        with orm.db_session:
            m_guild.system_ch_city_setup = str(new_channel.id)
            m_guild.msg_city_setup_id = str(msg.id)

    async def help_re_create(
        self: "Defence", channel: TextChannel, m_guild: Guilds
    ) -> None:
        """
        Re-creation of the system <<help>> channel
        """
        new_channel = await self.new_channel(channel)
        city_setup = self.bot.get_channel(m_guild.system_ch_city_setup)
        await create_system_help_msg(new_channel, city_setup)

        with orm.db_session:
            m_guild.system_ch_help = str(new_channel.id)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self: "Defence", channel: TextChannel) -> None:
        """
        Event processing channel deletion
        """
        with orm.db_session:
            m_guild: Guilds = Guilds.get(id=str(channel.guild.id))

            if m_guild is None or m_guild.frozen:
                return None

            await self._log(
                'delete channel from:', channel.guild.id, 
                channel.guild.name, 'channel:', channel.id, 
                channel.name
            )

            guild_channels = {
                "system_ch_category": int(m_guild.system_ch_category),
                "system_ch_city_setup": int(m_guild.system_ch_city_setup),
                "system_ch_help": int(m_guild.system_ch_help),
            }
            for k, v in guild_channels.items():
                if channel.id == v: 
                    await self.func_system_list[k](channel, m_guild)

            if m_guild.clans is None:
                return None

            for _id in m_guild.clans:
                with contextlib.suppress(Exception):
                    clan: Clans = Clans.get(id=int(_id))
                    clan_channels = {
                        k: v for k, v in {
                            "category_id": int(clan.category_id),
                            "channel_logs_id": int(clan.channel_logs_id),
                            "channel_wallet_id": int(clan.channel_wallet_id),
                            "channel_marketplace_id": int(clan.channel_marketplace_id),
                            "channel_statistics_id": int(clan.channel_statistics_id),
                            "channel_engage_id": int(clan.channel_engage_id),
                            "channel_join_id": int(clan.channel_join_id),
                            "channel_help_id": int(clan.channel_help_id),
                        }
                    }
                    for k, v in clan_channels.items():
                        if channel.id == v:
                            await self.func_clan_list[k](channel, clan)

    @commands.Cog.listener()
    async def on_guild_role_delete(self: "Defence", role: Role) -> None:
        """
        Event processing the removal of roles
        """
        with orm.db_session:
            m_guild: Guilds = Guilds.get(id=str(role.guild.id))

            if m_guild is None or m_guild.frozen:
                return None

            await self._log(
                'delete role from:', role.guild.id,
                role.guild.name, 'role:', role.id, role.name
            )

            guild_roles = {k: v for k, v in {
                "role_ether": int(m_guild.role_ether),
                "role_nods": int(m_guild.role_nods),
            }}

            for k, v in guild_roles.items():
                if role.id == v:
                    await self.role_system_re_create(role, m_guild, k)

            if m_guild.clans is None:
                return None
            
            for _id in m_guild.clans:
                try:
                    clan: Clans = Clans.get(id=int(_id))
                    clan_roles = {k: v for k, v in {
                        "role_owner_id": int(clan.role_owner_id),
                        "role_support_id": int(clan.role_support_id),
                        "role_nods_id": int(clan.role_nods_id),
                    }}
                    for k, v in clan_roles.items():
                        if role.id == v:
                            await self.role_clan_re_create(role, clan, k)

                except Exception as e:
                    await self._error(e)

    @commands.Cog.listener()
    async def on_member_update(self, before, after) -> None:
        """
        Event processing user update, checking for roles
        """
        if before.roles == after.roles:
            return None
        
        roles = list(set(before.roles) - set(after.roles))
        add_roles = list(set(after.roles) - set(before.roles))

        with orm.db_session:
            for role in roles + add_roles:
                m_guild: Guilds = Guilds.get(id=str(role.guild.id))
                
                if m_guild is None or m_guild.frozen:
                    return None

                if role.id == int(m_guild.role_ether) and role.guild.get_role(role.id) is not None:
                    member: Members = Members.get(id=str(after.id))
                    if member.ether_status:
                        await after.add_roles(role)
                    else:
                        await after.remove_roles(role)

                if role.id == int(m_guild.role_nods) and role.guild.get_role(role.id) is not None:
                    member: Members = Members.get(id=str(after.id))
                    if member.nods_status:
                        await after.add_roles(role)
                    else:
                        await after.remove_roles(role)

                if m_guild.clans is None:
                    return None

                for _id in m_guild.clans:
                    with contextlib.suppress(Exception):
                        clan: Clans = Clans.get(id=int(_id))
                        
                        clan_roles = {
                            "role_owner_id": int(clan.role_owner_id),
                            "role_support_id": int(clan.role_support_id),
                            "role_nods_id": int(clan.role_nods_id),
                        }

                        for k, v in clan_roles.items():
                            if role.id == v:
                                if role.guild.get_role(role.id) is not None:
                                    if after.id in clan_roles[k]:
                                        await after.add_roles(role)
                                        continue
                                    await after.remove_roles(role)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after) -> None:
        """
        Event processing role changes, checking the rights of the bot
        """
        if not before.is_bot_managed():
            return None

        if not after.permissions.administrator:
            await self._log('guild remove perms admin:', before.guild.id, before.guild.name)
            await self.frozen_guild(before.guild)

        elif not before.permissions.administrator and after.permissions.administrator:
            await self._log('guild returned perms admin:', before.guild.id, before.guild.name)
            await self.defrost_guild(before.guild)

    @classmethod
    async def frozen_guild(cls: "Defence", guild: Guild) -> None:
        """
        Freezing the server and the clans that are in it
        """
        with orm.db_session:
            m_guild: Guilds = Guilds.get(id=str(guild.id))
            m_guild.frozen = True

            await cls._log(
                cls, 'guild is frozen:', guild.id, guild.name, 
                'owner:', guild.owner_id, guild.owner.name
            )

            guild_clans = m_guild.clans

            with contextlib.suppress(Exception):
                for clan in guild_clans:
                    clan: Clans = Clans.get(_id=int(clan))
                    clan.frozen = True
                    await cls._log(
                        cls, 'clan is frozen:', clan.token, 
                        'owner:', clan.owner_clan
                    )
                    RatingClans.get(id=str(clan._id))

                TransactionMain(
                    type="frost_guild",
                    date=datetime.datetime.now(),
                    guild=str(guild.id),
                    owner=str(guild.owner_id),
                    clans=guild_clans
                )

    async def __delete_category(
        self: "Defence", guild: Guild, _guild_channels: dict
    ) -> None:
        for _, v in _guild_channels.items():
            with contextlib.suppress(Exception):
                await guild.get_channel(v).delete()

        with orm.db_session:
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

    async def defrost_guild(self: "Defence", guild: Guild) -> None:
        """
        Freezing the server and the clans that are in it
        """
        with orm.db_session:
            m_guild: Guilds = Guilds.get(id=str(guild.id))
            if m_guild is None or m_guild.frozen or not guild.self_role.permissions.administrator:
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
                    with contextlib.suppress(Exception):
                        clan: Clans = Clans.get(_id=int(clan))
                        clan.frozen = False
                        await self._log(
                            'clan is defrost:', clan.token, 
                            'owner:', clan.owner_clan
                        )

                TransactionMain(
                    type="defrost_guild",
                    date=datetime.datetime.now(),
                    guild=str(guild.id),
                    owner=str(guild.owner_id),
                    clans=guild_clans
                )

            except Exception as e:
                await self._error(
                    'defrost error:', e, 'guild:', 
                    guild.id, guild.name
                )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Defence(bot))
    print(f'=== cogs {Defence.__name__} loaded ===')
