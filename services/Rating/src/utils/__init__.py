import contextlib

import typing as ty

import pony.orm as orm

from datetime import datetime

from discord import (
    Guild, Message, Member,
    TextChannel, Embed, Forbidden,
    PermissionOverwrite
)
from discord_components import Interaction, Button
from discord.ext.commands import Bot

from .messages import *
from .. import discord_config, ether_city_channels
from ..database import (
    Members, WhiteListUsers, Guilds, TransactionMain
)

RED_COLOR = 0xf75151
GREEN_COLOR = 0xdec5b
INVISIBLE_COLOR = 0x2f3136
DEFAULT_COLOR = 0x23272A
AVOCADO_COLOR = 0xd3ffb5
BLUE_COLOR = 0x6badf7


def float_round(num: int, places: int = 0) -> float:
    """
    The function returns a number with places characters after the decimal point
    """
    return round(num * (10 ** places)) / float(10 ** places)


async def send_log_channel(
    title: str, text: str, bot: Bot
) -> None:
    """
    Отправка сообщений в log channel ether city
    """
    with contextlib.suppress(Exception):
        guild: Guild = bot.get_guild(discord_config['server_main'])
        channel: TextChannel = guild.get_channel(ether_city_channels['log'])
        emb = discord.Embed(
            title=title,
            description=text,
            colour=GREEN_COLOR
        )
        emb.set_footer(text='Ξther City Network')
        await channel.send(embed=emb)


async def send_embed(
    text: str, title: str = None, color: int = DEFAULT_COLOR, 
    member: Member = None, channel: TextChannel = None, 
    footer: str = None, interaction: Interaction = None
) -> ty.Union[Message, None]:
    """
    Sending messages from embed
    """
    if title is not None:
        emb = Embed(
            title=title,
            description=text,
            colour=color
        )
    else:
        emb = Embed(
            description=text,
            colour=color
        )

    emb.set_footer(
        text='Ξther City Network'
    ) if footer is None else emb.set_footer(text=footer)

    try:
        out = channel if channel is not None else member
        msg = await out.send(embed=emb)
        return msg

    except Forbidden:
        if interaction is not None:
            await interaction.respond(
                embed=Embed(
                    description='I was trying to send you DM. But it seems blocked.',
                    colour=RED_COLOR
                )
            )
            print(
                'lock dm in user: ', interaction.user.id, 
                interaction.user.name, interaction.component.label
            )
        return None


async def white_list_guild_owners(guild: Guild) -> None:
    """
    Function for checking the server for presence in the white list
    """
    if discord_config['test']:
        return True

    if not WhiteListUsers.select().exists() and \
        WhiteListUsers.get(id=str(guild.owner.id)) is not None:
        return True

    await send_embed(
        text='Access denied',
        color=RED_COLOR,
        member=guild.owner
    )
    await guild.leave()
    print(
        'Leave bot from guild:', guild.id, guild.name, 
        'owner:', guild.owner_id, guild.owner.name
    )


async def add_guild_to_database(guild: Guild) -> None:
    """
    Adding a server to the database
    """
    with orm.db_session:
        Guilds(
            id=str(guild.id),
            name=guild.name,
            created_at=guild.created_at,
            owner=guild.owner.name,
            owner_id=str(guild.owner_id),
            occasion_creating_clan=False,
            frozen=False,
            verification=False
        )
    print('add server to base: guild: ', guild.id, guild.name)


async def create_category_guild(guild: Guild) -> None:
    """
    Creating system categories for the server
    """
    overwrites_owner = {
        guild.default_role: PermissionOverwrite(
            read_messages=False, send_messages=False
        )
    }
    category = await guild.create_category(
        name='Ether-city system', position=0, 
        overwrites=overwrites_owner
    )
    ch_city_setup = await guild.create_text_channel(
        name='city-setup', overwrites=overwrites_owner, category=category
    )
    ch_help = await guild.create_text_channel(
        name='help', overwrites=overwrites_owner, category=category
    )
    await create_system_help_msg(ch_help, ch_city_setup)
    msg_setup = await create_city_setup_msg(ch_city_setup, ch_help)

    with orm.db_session:
        guild = Guilds.get(id=str(guild.id))
        guild.system_ch_category = category.id
        guild.system_ch_city_setup = ch_city_setup.id
        guild.system_ch_help = ch_help.id
        guild.system_ch_city_setup_msg = msg_setup.id


async def add_to_database_main_guild(guild: Guild) -> None:
    """
    Adding the main server to the database
    """
    with orm.db_session:
        Guilds(
            id=str(guild.id),
            name=guild.name,
            created_at=guild.created_at,
            owner=guild.owner.name,
            owner_id=str(guild.owner_id),
            role_nods=str(discord_config['role_nods']),
            role_ether=str(discord_config['role_ether']),
            frozen=False,
            main_server=True,
        )
    print('add server to base: guild: ', guild.id, guild.name)


async def create_main_server_rating_wallet(guild: Guild) -> None:
    """
    Function for creating rating wallet channels on ether city
    """
    if guild.id != discord_config['server_main']:
        return None
    
    channel_rating = guild.get_channel(ether_city_channels['rating'])
    channel_wallet = guild.get_channel(ether_city_channels['wallet'])

    msg_wallet = await channel_wallet.send(
        embed=discord.Embed(
            title='Personal Wallet',
            description='Check your current balance by pressing the "Balance" '
                        'button. In order to send your tokens to any player within '
                        'Ether City ecosystem use the "Send Tokens" button',
            color=INVISIBLE_COLOR
        ),
        components=[
            [
                Button(style=ButtonStyle.blue, label='Balance'),
                Button(style=ButtonStyle.blue, label='Send'),
                Button(style=ButtonStyle.blue, label='My cities')
            ]
        ]
    )

    msg_rating = await channel_rating.send(
        embed=discord.Embed(
            title='Leaderboards',
            description='Check the Ether City\'s Top-10 players and cities',
            colour=INVISIBLE_COLOR
        ),
        components=[
            [
                Button(style=ButtonStyle.blue, label='Players'),
                Button(style=ButtonStyle.blue, label='Cities'),
            ]
        ]
    )

    with orm.db_session:
        guild = Guilds.get(id=str(guild.id))
        guild.msg_rating_id = str(msg_rating.id)
        guild.msg_wallet_id = str(msg_wallet.id)


async def add_user_to_database(member: Member) -> None:
    """
    Adding a user to the database
    """
    with orm.db_session:
        Members(
            id=str(member.id),
            name=member.name,
            created_at=member.created_at,
            ether_status=False,
            nods_status=False,
            vi0_status=False,
            vi1_status=False,
            exp_all="0",
            exp_rank="25",
            lvl_rank="1",
            tokens="5.0",
            daily_exp_msg_limit="50",
            daily_exp_msg_limit_time="0"
        )

    print('add user to base: ', member.id, member.name)

    await send_embed(
        title='You are the Decentralized Citizen of Ether City',
        text='And your primary role is Vi1. It grants you access to a personal wallet, Ether City Tokens and other perks. Go back to Ether City Server for more info.',
        color=GREEN_COLOR,
        member=member
    )

    with orm.db_session:
        TransactionMain(
            type='role_vi1_get',
            date=datetime.now(),
            user_id=str(member.id),
        )

    await member.add_roles(
        member.guild.get_role(discord_config['role_vi1'])
    )
    print('user get role vi1: ', member.id, member.name)
