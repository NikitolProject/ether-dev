import asyncio

import discord

from discord.ext import commands, tasks
from discord_components import Interaction

from . import *
from .utils import *
from .utils.messages import *
from .database import *


class Buttons(BasicCog, name='buttons'):

    used_button_users = {}
    user_bans = []

    user_used = []
    used_button = []

    used_join = []
    used_button_transfer = []
    used_create_city = []
    used_top_up = []
    used_local = []
    used_global = []
    used_market = []

    def __init__(self: "Buttons", bot: commands.Bot) -> None:
        super().__init__(bot)
        self.clear_used_button_user.start()

    async def __check_bot_admin_perm(self: "Buttons", guild: Guild) -> bool:
        bot_member: Member = guild.get_member(self.bot.user.id)
        if bot_member.guild_permissions.administrator:
            return True

    async def check_guild_for_perms(self: "Buttons", guild: Guild) -> bool:
        """
        Checking the server for the necessary bot rights
        """
        with orm.db_session:
            m_guild: Guilds = Guilds.get(id=str(guild.id))

        if guild is not None and not m_guild.frozen and await self.__check_bot_admin_perm(guild):
            return True
        return False

    @classmethod
    async def check_member_in_clan(cls: "Buttons", interaction: Interaction, mo_channel: str) -> bool:
        """
        Checking the user for communion with the clan
        """
        with contextlib.suppress(Exception):
            if interaction.guild.id != discord_config['server_main']:
                with orm.db_session:
                    clan: Clans = Clans.get(**{mo_channel: interaction.channel.id})

                if clan is not None and str(interaction.user.id) not in clan.nods and str(interaction.user.id) != clan.owner_clan:
                    return False
                
                return True
        return False

    @tasks.loop(minutes=2)
    async def clear_used_button_user(self: "Buttons") -> None:
        """
        Event clearing the list of recent button clicks
        """
        await self._log(
            "An event has started clearing the list of recent button clicks"
        )

        self.used_button_users.clear()

    @clear_used_button_user.before_loop
    async def before_clear_used_button_user(self: "Buttons") -> None:
        """
        Initializing the clear_used_button_user event
        """
        await self.bot.wait_until_ready()

    @classmethod
    async def send_button_error(cls: "Buttons", e: str, interaction: Interaction) -> None:
        """
        Handler for errors that occur when the button is clicked
        """
        await cls._error(
            cls, f"###Button error: {e}, {interaction.user.name},"
            f"{interaction.user.id}, {interaction.component.label}"
        )

    async def check_button(self: "Buttons", interaction: Interaction) -> ty.Union[bool, None]:
        """
        Handler for button clicks, checking for limit
        """
        user = self.used_button_users.get(interaction.user.id)
        
        if user is None:
            self.used_button_users.update({interaction.user.id: [interaction.component.label] + [1]})
        elif user[0] == interaction.component.label:
            if user[1] >= 10:
                self.user_bans.append(interaction.user.id)
                await send_interaction_respond(
                    interaction, discord.Embed(
                        description='You\'ve exceeded the amount of attempts (10). 15 min. cooldown is applied.',
                        colour=RED_COLOR
                    )
                )
                await self._log(
                    f'get click limit: {str(interaction.user.name)} '
                    f'{str(interaction.user.id)} {str(interaction.component.label)}'
                )
                await asyncio.sleep(20)
                self.user_bans.remove(interaction.user.id)
                return True

            self.used_button_users.update({interaction.user.id: [interaction.component.label] + [user[1] + 1]})
        else:
            self.used_button_users.update({interaction.user.id: [interaction.component.label] + [1]})

    @commands.Cog.listener()
    async def on_button_click(self: "Buttons", interaction: Interaction) -> None:
        """
        The main event reacting to the click on the button
        """
        with orm.db_session:
            member: Members = Members.get(id=str(interaction.user.id))

        await self._log(
            f"Button click {interaction.user.name}, "
            f"{interaction.user.id}, {interaction.component.label}"
        )

        if member is None:
            return None

        buttons_list = (
            'Balance',
            'Send',
            'City',
            'Join',
            'Top up',
            'Refresh',
            'Nods',
            'Cities',
            'Players',
            'Local',
            'Global',
            'My cities'
        )

        if not interaction.component.label in buttons_list:
            return None

        if not await self.check_guild_for_perms(interaction.guild):
            await interaction.respond(
                embed=discord.Embed(
                    description='You\'ve exceeded the amount of attempts (10). 15 min. cooldown is applied.',
                    colour=RED_COLOR
                ).set_footer(text='Ξther City Network')
            )
            return None

        if interaction.user.id in self.user_bans:
            return None

        if await self.check_button(interaction):
            return None

        await asyncio.sleep(0.1)
        if interaction.component.label == 'Balance':
            try:
                if not await self.check_member_in_clan(interaction, 'channel_wallet_id'):
                    await self.bot.get_cog('clans').member_profile(interaction)
            except Exception as e:
                await self.send_button_error(e, interaction)

        elif interaction.component.label == 'Send':
            if interaction.user.id not in self.user_used:
                if interaction.user.id not in self.used_button_transfer:
                    if not await self.check_member_in_clan(interaction, 'channel_wallet_id'):
                        try:
                            self.user_used.append(interaction.user.id)
                            self.used_button_transfer.append(interaction.user.id)
                            stat = await self.bot.get_cog('clans').tokens_transfer(interaction)
                            self.user_used.remove(interaction.user.id)
                            if stat:
                                await asyncio.sleep(600)
                            self.used_button_transfer.remove(interaction.user.id)
                        except Exception as e:
                            self.user_used.remove(interaction.user.id)
                            self.used_button_transfer.remove(interaction.user.id)
                            await self.send_button_error(e, interaction)

        elif interaction.component.label == 'City':
            if interaction.user.id not in self.used_create_city:
                if interaction.user == interaction.guild.owner:
                    try:
                        self.used_create_city.append(interaction.user.id)
                        stat = await self.bot.get_cog('server_setup').create_city(interaction)
                        if stat is None:
                            await asyncio.sleep(600)
                        self.used_create_city.remove(interaction.user.id)
                    except Exception as e:
                        self.used_create_city.remove(interaction.user.id)
                        await self.send_button_error(e, interaction)

        elif interaction.component.label == 'Join':
            if interaction.user.id not in self.user_used:
                if interaction.user.id not in self.used_join:
                    if await self.check_member_in_clan(interaction, 'channel_join_id') == 0:
                        try:
                            self.user_used.append(interaction.user.id)
                            self.used_join.append(interaction.user.id)
                            stat = await self.bot.get_cog('clans').join_to_clan(interaction)
                            self.user_used.remove(interaction.user.id)
                            if stat is None:
                                await asyncio.sleep(600)
                            self.used_join.remove(interaction.user.id)
                        except Exception as e:
                            self.user_used.remove(interaction.user.id)
                            self.used_join.remove(interaction.user.id)
                            await self.send_button_error(e, interaction)

        elif interaction.component.label == 'Top up':
            if interaction.user.id not in self.user_used:
                if interaction.user.id not in self.used_top_up:
                    if not await self.check_member_in_clan(interaction, 'channel_wallet_id'):
                        try:
                            self.user_used.append(interaction.user.id)
                            self.used_top_up.append(interaction.user.id)
                            stat = await self.bot.get_cog('clans').top_up(interaction)
                            self.user_used.remove(interaction.user.id)
                            if stat:
                                await asyncio.sleep(600)
                            self.used_top_up.remove(interaction.user.id)
                        except Exception as e:
                            self.user_used.remove(interaction.user.id)
                            self.used_top_up.remove(interaction.user.id)
                            await self.send_button_error(e, interaction)

        elif interaction.component.label == 'Refresh':
            try:
                if not await self.check_member_in_clan(interaction, 'channel_statistics_id'):
                    await self.bot.get_cog('clans').stats_clan(interaction)
            except Exception as e:
                await self.send_button_error(e, interaction)

        elif interaction.component.label == 'Nods':
            try:
                if not await self.check_member_in_clan(interaction, 'channel_statistics_id'):
                    await self.bot.get_cog('clans').members_clan(interaction)
            except Exception as e:
                await self.send_button_error(e, interaction)

        elif interaction.component.label == 'My cities':
            try:
                if not await self.check_member_in_clan(interaction, 'channel_wallet_id'):
                    await self.bot.get_cog('clans').member_cities(interaction)
            except Exception as e:
                await self.send_button_error(e, interaction)

        elif interaction.component.label == 'Cities':
            try:
                if not await self.check_member_in_clan(interaction, 'channel_statistics_id'):
                    await self.bot.get_cog('clans').top_clans(interaction)
            except Exception as e:
                await self.send_button_error(e, interaction)

        elif interaction.component.label == 'Players':
            try:
                await self.bot.get_cog('clans').top_members(interaction)
            except Exception as e:
                await self.send_button_error(e, interaction)
        
        elif interaction.component.label == 'Local':
            if interaction.user.id not in self.user_used:
                if interaction.user.id not in self.used_local:
                    if not await self.check_member_in_clan(interaction, 'channel_marketplace_id'):
                        try:
                            self.user_used.append(interaction.user.id)
                            self.used_local.append(interaction.user.id)
                            stat = await self.bot.get_cog('marketplace').market_local_button(interaction)
                            self.user_used.remove(interaction.user.id)
                            if stat:
                                await asyncio.sleep(600)
                            self.used_local.remove(interaction.user.id)
                        except Exception as e:
                            self.user_used.remove(interaction.user.id)
                            self.used_local.remove(interaction.user.id)
                            await self.send_button_error(e, interaction)

        elif interaction.component.label == 'Global':
            if interaction.user.id not in self.user_used:
                if interaction.user.id not in self.used_global:
                    if not await self.check_member_in_clan(interaction, 'channel_marketplace_id'):
                        try:
                            self.user_used.append(interaction.user.id)
                            self.used_global.append(interaction.user.id)
                            stat = await self.bot.get_cog('marketplace').market_global_button(interaction)
                            self.user_used.remove(interaction.user.id)
                            if stat:
                                await asyncio.sleep(3600)
                            self.used_global.remove(interaction.user.id)
                        except Exception as e:
                            self.user_used.remove(interaction.user.id)
                            self.used_global.remove(interaction.user.id)
                            await self.send_button_error(e, interaction)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Buttons(bot))
    print(f'=== cogs {Buttons.__name__} loaded ===')
