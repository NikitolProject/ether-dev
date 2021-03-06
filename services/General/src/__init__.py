import os
import contextlib

import logging

from discord.ext import commands

discord_config = {
    'test': False,
    'oauth2': 'https://discord.com/api/oauth2/authorize?'
                'client_id=810134081530363904&permissions=8&scope=bot',
    'invite_link_to_main': 'https://discord.gg/2TCuBGhyN6',
    'server_main': 905454076832149505,
    'security': True,
    'create_msg_rating_wallet': True,
    'super_admins': [505744767095930881, 798613956863590430, 805456415237603338],
    'role_vi1': 905469640216555612,
    'role_ether': 905469675448717402,
    'role_nods': 905469723599339541,
    'color_ether': 0xf56e6e,
    'color_nods': 0x4eee6b,
}

ether_city_channels = {
    'st_member_count': 905470266245779496,
    'st_ect_count': 905470693926379530,
    'st_clan_count': 905470933702180866,
    'rating': 905471247163461632,
    'wallet': 905471317036388402,
    'vi1-everyone': 905471426109276180,
    'marketplace': 905471522943168574,
    'log': 905471645244874753,
    'cities': 905471696943849532,
    'validate': 913894720562921512
}


class BasicCog(commands.Cog):

    logging.basicConfig(
        level=logging.DEBUG, filename=f'{os.path.abspath(os.curdir)}/services/General/bot.log', 
        format='%(asctime)s %(levelname)s:%(message)s'
    )

    logger = logging.getLogger(__name__)

    def __init__(self: "BasicCog", bot: commands.Bot) -> None:
        self.bot = bot

    async def _log(self: "BasicCog", message: str, *args: tuple) -> None:
        with contextlib.suppress(Exception):
            message += ' ' + ' '.join([str(idx) for idx in args])
            self.logger.info(message)
            print(message)

    async def _error(self: "BasicCog", message: str, *args) -> None:
        with contextlib.suppress(Exception):
            message += ' ' + ' '.join([str(idx) for idx in args])
            self.logger.error(message)
            print(message)
