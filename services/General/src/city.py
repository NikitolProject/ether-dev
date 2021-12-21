import asyncio
from os import name

import discord
from discord import guild
from discord import colour

from discord_components import Button, ButtonStyle, Interaction

from . import BasicCog, discord_config, ether_city_channels
from .utils import *
from .database import *


class ServerSetup(BasicCog, name='server_setup'):

    @classmethod
    async def __emb_error(
        cls: "ServerSetup", f_interaction: Interaction, 
        errors: int, text: str
    ) -> discord.Embed:
        if errors >= 5:
            return
        await send_embed(
            text=f"You were unsuccessful, {f_interaction.user.name}. Ether City's "
                 f"guidelines won't allow me to register that name. Please try again.",
            title=f'{text}',
            color=RED_COLOR,
            channel=f_interaction.user,
            footer=f'{errors}/5 attempts'
        )

    async def create_nft(self: "ServerSetup", f_interaction: Interaction) -> None:
        """
        Linking a smart contract to a city
        """
        await self._log(
            f"{f_interaction.user} is trying to create a new smart contract"
        )

        with orm.db_session:
            guild: Guilds = Guilds.get(id=str(f_interaction.guild.id))

            if guild is None:
                await f_interaction.respond(
                    embed=discord.Embed(
                        title='The city has not been created',
                        description='Your city has not been created, please create a city first.',
                        color=RED_COLOR
                    )
                )
                return None

            dm = await f_interaction.author.create_dm()

            await f_interaction.respond(
                embed=discord.Embed(
                    description=f"Please go to the [bot's private messages](https://discord.com/channels/@me/{dm.id})",
                    color=discord.Colour.dark_blue()
                )
            )

            await send_embed(
                text="Enter the address of the smart contract that you want to link to the city",
                color=discord.Color.dark_blue(),
                interaction=f_interaction,
                member=f_interaction.user
            )

            try:
                address = await f_interaction.wait_for(
                    'message',
                    check=lambda m: m.author == f_interaction.user,
                    timeout=60
                )
            except asyncio.TimeoutError:
                await send_embed(
                    text='You have not entered the address in time. Try again.',
                    color=discord.Color.dark_blue(),
                    interaction=f_interaction,
                    member=f_interaction.user
                )
                return None

            pass

    async def create_city(self: "ServerSetup", f_interaction: Interaction) -> None:
        """
        Creating a city in Ether city(button)
        """
        with orm.db_session:
            if Guilds.select().exists() and len(Members.get(id=str(f_interaction.user.id)).verification_owner_servers) >= 1:
                await f_interaction.respond(
                    embed=discord.Embed(
                        description='1 server = 1 city and vice versa',
                        colour=RED_COLOR
                    ).set_footer(text='Ξther City Network')
                )
                return None

            if float(Members.get(id=str(f_interaction.user.id)).tokens) < 100.0:
                await f_interaction.respond(
                    embed=discord.Embed(
                        description='I couldn\'t reserve 100 ECT for your city\'s vault. Please top up the wallet in order to proceed.\n'
                                    f'If you need more details go to {f_interaction.guild.get_channel(int(Guilds.get(id=str(f_interaction.guild.id)).system_ch_help)).mention} channel',
                        colour=RED_COLOR
                    ).set_footer(text='Ξther City Network')
                )
                return True

            dm = await f_interaction.author.create_dm()

            await f_interaction.respond(
                embed=discord.Embed(
                    description=f"Please go to the [bot's private messages](https://discord.com/channels/@me/{dm.id})",
                    color=discord.Colour.dark_blue()
                )
            )

            await self._log(
                f'start create city: {f_interaction.user.id}, {f_interaction.user.name} '
                f'guild: {f_interaction.guild.id}, {f_interaction.guild.name}'
            )
            errors = 0

            try:
                await send_embed(
                    text='Excellent, it looks like you have the necessary funds '
                         'available to continue. Now for the fun part. Please enter '
                         'a name for your city (up to 30 characters.)',
                    color=INVISIBLE_COLOR,
                    interaction=f_interaction,
                    member=f_interaction.user)
                await invisible_respond(f_interaction)
            except discord.errors.Forbidden:
                await f_interaction.respond(
                    embed=discord.Embed(
                        description='I\'m sorry, but I can\'t send you a message. Please allow me to send messages in your DMs.',
                        colour=RED_COLOR
                    ).set_footer(text='Ξther City Network')
                )
                return None

            while errors < 5:
                try:
                    _name: discord.Message = await self.bot.wait_for(
                        'message', timeout=120,
                        check=lambda m: m.author == f_interaction.user and m.channel.type == discord.ChannelType.private
                    )
                except asyncio.TimeoutError:
                    await timeout_error(f_interaction.user)
                    return True

                _name: str = _name.content
                if _name is None:
                    errors += 1
                    await self.__emb_error(f_interaction, errors, 'Invalid name. Please retry!')
                    continue
                    
                elif len(_name) < 3:
                    errors += 1
                    await self.__emb_error(f_interaction, errors, 'Short name')
                    continue

                elif len(_name) > 30:
                    errors += 1
                    await self.__emb_error(f_interaction, errors, 'Long name')
                    continue

                elif not check_symbols(_name):
                    errors += 1
                    await self.__emb_error(f_interaction, errors, 'The city name should not include any special characters')
                    continue

                if CheckBusy.select().exists():
                    for n in CheckBusy.get(status='busy').names:
                        if n.split('.')[1] == _name.lower():
                            errors += 1
                            await self.__emb_error(f_interaction, errors, 'The name is taken!')
                            return None

                msg = await send_embed(
                    text=f'I have good news, {_name} has been accepted by the Ether City registrar office. Everything is ready, {f_interaction.user.name}. Do you wish to continue and create this city?',
                    color=GREEN_COLOR,
                    member=f_interaction.user
                )
                await msg.edit(
                    components=[
                        [
                            Button(style=ButtonStyle.green, label='Agree'),
                            Button(style=ButtonStyle.red, label='Disagree')
                        ]
                    ]
                )

                try:
                    msg_interaction = await self.bot.wait_for(
                        'button_click', timeout=180,
                        check=lambda m: m.channel.type == discord.ChannelType.private and m.message == msg and m.user == f_interaction.user
                    )
                except asyncio.TimeoutError:
                    await msg.delete()
                    return True

                if msg_interaction.component.label == 'Disagree':
                    await invisible_respond(msg_interaction)
                    await send_embed(
                        text='I see. If you change your mind, please return here and we can start again.',
                        color=GREEN_COLOR,
                        member=f_interaction.user
                    )
                    return True

                if msg_interaction.component.label == 'Agree':
                    await invisible_respond(msg_interaction)
                    if float(Members.get(id=str(f_interaction.user.id)).tokens) >= 100:
                        await self.success_create_city(f_interaction, _name)
                        return True

                    errors += 1
                    emb = discord.Embed(
                        description=f'My apologies {f_interaction.user.name}, it seems that the required 100 ECT is no longer in your wallet. You no longer have enough to fund {_name}. Please add funds to your wallet and try again.',
                        colour=RED_COLOR
                    ).set_footer(text=f'{errors}/5 attempts')
                    _msg = await f_interaction.user.send(
                        embed=emb,
                        components=[
                            [
                                Button(style=ButtonStyle.blue, label='Retry')
                            ]
                        ]
                    )
                    
                    while errors < 5:
                        try:
                            _msg_interaction = await self.bot.wait_for('button_click', timeout=180,
                                                                        check=lambda m: m.channel.type == discord.ChannelType.private and m.message == _msg and m.user == f_interaction.user)
                        except asyncio.TimeoutError:
                            f_interaction.user.send(
                                embed=discord.Embed(
                                    description='I apologize, your attempts have initiated a system cooldown. Please check back in 10 minutes and make sure your wallet is funded with at least 100 ECT.',
                                    colour=RED_COLOR
                                ).set_footer(text='Ξther City Network')
                            )
                            await msg.delete()
                            return True
                        
                        if _msg_interaction.component.label == 'Retry':
                            await invisible_respond(_msg_interaction)

                            if float(Members.get(id=str(f_interaction.user.id)).tokens) >= 100:
                                await _msg.delete()
                                await self.success_create_city(f_interaction, _name)
                                return True

                            errors += 1
                            if errors >= 5:
                                await _msg.delete()
                                break

                            await _msg.edit(
                                embed=discord.Embed(
                                    description="Unfortunately, I still don't see the funds available. Please make sure you have funded your wallet, I'll wait here.",
                                    colour=RED_COLOR
                                ).set_footer(text=f'{errors}/5 attempts')
                            )
                            continue

                await send_embed(
                    text="There's a problem. You've made 5 unsuccessful attempts and initiated a system cooldown. Please wait 10 minutes and try again.",
                    color=RED_COLOR,
                    channel=f_interaction.user
                )
                return None

    async def success_create_city(self: "ServerSetup", f_interaction: Interaction, name: str) -> None:
        """
        Creating a city in Ether City (2-step)
        """
        await self._log(
            f'start create city 2 step\nname: {name}, '
            f'{f_interaction.user.id}, {f_interaction.user.name},\n'
            f'guild: {f_interaction.guild.id}, {f_interaction.guild.name}'
        )

        with orm.db_session:
            if not CheckBusy.select().exists():
                CheckBusy(
                    names=[],
                    status="busy",
                    incs="0000",
                    tokens=[],
                    incs_escrow="0"
                )

            token = int(CheckBusy.get(status='busy').incs) + 1
            token = '%04d' % token
            
            Ethers(
                owner_id=str(f_interaction.user.id),
                name=name,
                token=token,
                status_clan=False
            )
            ether: Ethers = Ethers.get(name=name)

            check_busy: CheckBusy = CheckBusy.get(status='busy')
            check_busy.names.append(f"{str(f_interaction.user.id)}.{name.lower()}")
            check_busy.tokens.append(f"{str(f_interaction.user.id)}.{token}")
            check_busy.incs = token
            if not Members.get(id=str(f_interaction.user.id)).ether_status:
                Members.get(id=str(f_interaction.user.id)).ether_status = True

                # await self.bot.get_cog('rating').check_status(
                #     f_interaction.guild.get_member(f_interaction.user.id)
                # )
            await self.create_clan(f_interaction, ether)

    async def create_clan(self: "ServerSetup", f_interaction: Interaction, ether: Ethers) -> None:
        """
        Creating a city (the last step)
        """
        await self._log(
            f'start create city 3 step: {f_interaction.guild.id}, '
            f'{f_interaction.guild.name}, guild: {f_interaction.guild.id}, '
            f'{f_interaction.guild.name}'
        )

        with orm.db_session:
            role_owner = await f_interaction.guild.create_role(
                name='Ethers' + '.' + str(ether.token)
            )
            role_nods = await f_interaction.guild.create_role(
                name='Nods' + '.' + str(ether.token)
            )

            overwrites_nods = {
                f_interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                role_owner: discord.PermissionOverwrite(read_messages=True, manage_roles=False,
                                                        manage_messages=True),
                role_nods: discord.PermissionOverwrite(read_messages=True)
            }

            overwrites_all = {
                f_interaction.guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                role_nods: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                role_owner: discord.PermissionOverwrite(read_messages=True, send_messages=True,
                                                        manage_roles=False, manage_channels=False,
                                                        manage_messages=True)
            }

            overwrites_voice = {
                f_interaction.guild.default_role: discord.PermissionOverwrite(connect=False),
                role_nods: discord.PermissionOverwrite(connect=True),
                role_owner: discord.PermissionOverwrite(connect=True, manage_roles=True,
                                                        manage_channels=False, manage_messages=True)
            }

            overwrites_nods_view = {
                f_interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                role_owner: discord.PermissionOverwrite(read_messages=True, manage_roles=False, manage_messages=True),
                role_nods: discord.PermissionOverwrite(read_messages=True, send_messages=False)
            }

            category = await f_interaction.guild.create_category(name=str(ether.token) + ". " + str(ether.name), overwrites=overwrites_nods)
            channel_join = await f_interaction.guild.create_text_channel(name='Join', overwrites=overwrites_all, category=category)
            channel_engage = await f_interaction.guild.create_text_channel(name='engage', overwrites=overwrites_nods, category=category)
            channel_marketplace = await f_interaction.guild.create_text_channel(name='Marketplace', overwrites=overwrites_nods_view, category=category, slowmode_delay=3600)
            channel_wallet = await f_interaction.guild.create_text_channel(name='Wallet', overwrites=overwrites_nods_view, category=category)
            channel_statistics = await f_interaction.guild.create_text_channel(name='Stats', overwrites=overwrites_nods_view, category=category)
            channel_logs = await f_interaction.guild.create_text_channel(name='Logs', overwrites=overwrites_nods_view, category=category)
            channel_help = await f_interaction.guild.create_text_channel(name='Help', overwrites=overwrites_nods_view, category=category)
            channel_voice = await f_interaction.guild.create_voice_channel(name='voice', overwrites=overwrites_voice, category=category)
            msg_join = await create_join_msg(channel_join, ether.name)
            user: Members = Members.get(id=ether.owner_id)
            msg_statistics = await create_statistics_msg(channel_statistics, int(user.exp_all) + int(user.exp_rank))
            msg_wallet = await create_wallet_msg(channel_wallet)
            msg_marketplace = await create_marketplace_msg(channel_marketplace)
            await create_city_help_msg(channel_help, channel_marketplace, channel_wallet, channel_engage, channel_join, channel_statistics)
            invite_link = await channel_join.create_invite()
            if not Clans.select().exists() or Clans.get(name=name) is None:
                Clans(
                    owner_clan=ether.owner_id,
                    guild=str(f_interaction.guild.id),
                    name=ether.name,
                    token=ether.token,
                    invite_link=str(invite_link),
                    ether_id=str(ether._id),
                    frozen=False,
                    category_id=str(category.id),
                    msg_statistics_id=str(msg_statistics.id),
                    msg_wallet_id=str(msg_wallet.id),
                    msg_marketplace_id=str(msg_marketplace.id),
                    msg_join_id=str(msg_join.id),
                    channel_join_id=str(channel_join.id),
                    channel_engage_id=str(channel_engage.id),
                    channel_marketplace_id=str(channel_marketplace.id),
                    channel_wallet_id=str(channel_wallet.id),
                    channel_statistics_id=str(channel_statistics.id),
                    channel_logs_id=str(channel_logs.id),
                    channel_help_id=str(channel_help.id),
                    channel_voice_id=str(channel_voice.id),
                    role_owner_id=str(role_owner.id),
                    role_nods_id=str(role_nods.id),
                    color_clan="0x99AAB5",
                    total_exp="0",
                    vault0=[f"{f_interaction.user.id}:100:100"],
                    vault1="0",
                    total_income_from_mark_global="0",
                    other_channels=[],
                    nods=[],
                    supports=[],
                    history_nods=[],
                    history_supports=[]
                )
                RatingClans(
                    clan_id=str(Clans.get(ether_id=str(ether._id))._id),
                    token=ether.token,
                    name=ether.name,
                    invite_link=str(invite_link),
                    channel_statistics_id=str(channel_statistics.id),
                    msg_statistics_id=str(msg_statistics.id),
                    guild=str(f_interaction.guild.id),
                    members=[str(f_interaction.user.id)],
                    supports=[],
                    members_count="1",
                    total_exp="0",
                    clan_rate="0",
                    last_list=[]
                )

                orm.commit()
            user: Members = Members.get(id=ether.owner_id)
            user.verification_owner_servers.append(str(f_interaction.guild.id))
            user.clans_id.append(str(Clans.get(owner_clan=ether.owner_id)._id))
            user.exp_rank = str(int(user.exp_rank) + 500)
            user.tokens = str(float(user.tokens) - 100.0)
            orm.commit()
            ether: Ethers = Ethers.get(_id=ether._id)
            ether.status_clan = True
            ether._id_clan = str(Clans.get(ether_id=str(ether._id))._id)
            ether.guild_id = str(f_interaction.guild.id)
            ether._id_guild = str(Guilds.get(id=str(f_interaction.guild.id))._id)
            orm.commit()
            await f_interaction.guild.get_member(f_interaction.user.id).add_roles(role_owner)

            if not Guilds.get(id=str(f_interaction.guild.id)).verification:
                try:
                    system_role_ether = await f_interaction.guild.create_role(
                        name='Ethers', hoist=True, colour=discord_config['color_ether']
                    )
                    system_role_nods = await f_interaction.guild.create_role(
                        name='Nods', colour=discord_config['color_nods']
                    )
                    guild: Guilds = Guilds.get(id=str(f_interaction.guild.id))
                    guild.verification = True
                    guild.role_ether = str(system_role_ether.id)
                    guild.role_nods = str(system_role_nods.id)
                    orm.commit()

                except Exception as e:
                    await self._error(
                        f'start create city error: {e}, {f_interaction.user.id}, '
                        f'{f_interaction.user.name}, guild: {f_interaction.guild.id},' 
                        f'{f_interaction.guild.name}'
                    )

                await self.bot.get_cog('rating').check_members_guild(f_interaction.guild)
            guild: Guilds = Guilds.get(id=str(f_interaction.guild.id))
            guild.clans.append(str(Clans.get(ether_id=str(ether._id))._id))
            orm.commit()

            await self.bot.get_cog('rating').new_lvl(
                id=f_interaction.user.id, 
                send_msg=False
            )
            created_clan: Clans = Clans.get(owner_clan=str(ether.owner_id))
            await self.bot.get_cog('clans').update_top_members_in_clan(search=created_clan)

            await send_embed(
                title='Great news!',
                text=f'''
{ether.name} has been successfully created. 
You have, as humans say, leveled up. 
- Your city {ether.name} has been created 
- Your city's vault is now active with a balance of 100 ECT 
- Your profit vault is now active 
- Your role has changed. You are now an Ether 
- You have gained 500 XP
                ''',
                color=GREEN_COLOR,
                channel=f_interaction.user
            )

            await send_embed(
                title='Well then, Ether.',
                text="I look forward to helping your new city thrive. "
                     "You can now return to your server located on the "
                     "lefthand side of your screen. There you'll see new "
                     "channels associated with your city, including #wallet, "
                     "#marketplace, and #stats. I'll see you over there!",
                color=GREEN_COLOR,
                channel=f_interaction.user
            )

            await send_embed(
                text=f'{f_interaction.user.mention} topped up our Vault0 for **100** ECT.\n'
                    f'Vault0 balance: **100** ECT',
                color=INVISIBLE_COLOR,
                channel=channel_logs
            )

            update_ether: Ethers = Ethers.get(_id=ether._id)
            channel_cities = self.bot.get_channel(ether_city_channels['cities'])
            await send_embed(
                title=f'{created_clan.name}',
                text=f'Ethers: {self.bot.get_user(int(created_clan.owner_clan)).mention}\nLink: {created_clan.invite_link}',
                color=INVISIBLE_COLOR,
                channel=channel_cities       
            )
            for clan in Clans.select(lambda c: not c.frozen):
                try:
                    if clan._id == int(update_ether._id_clan):
                        continue

                    channel: TextChannel = self.bot.get_guild(int(clan.guild)).get_channel(
                        int(clan.channel_logs_id)
                    )

                    await channel.send(
                        embed=discord.Embed(
                            description=f'A new city has been founded. {ether.name} is now part of the Ether City Network.',
                            colour=BLUE_COLOR
                        )
                    )
                except Exception as e:
                    await self._error(
                        f'city create send msg to guilds error: {e}, {f_interaction.user.id}, '
                        f'{f_interaction.user.name}, guild: {f_interaction.guild.id}, {f_interaction.guild.name}'
                    )
            orm.commit()


def setup(bot: commands.Bot) -> None:
    bot.add_cog(ServerSetup(bot))
    print(f'=== cogs {ServerSetup.__name__} loaded ===')
