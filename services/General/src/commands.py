import discord

from discord.ext import commands

from . import BasicCog, discord_config
from .utils import *
from .utils.messages import add_to_white_list


class Commands(BasicCog, name="commands"):

    @commands.command(name='add_to_white_list')
    async def add_to_white_list(self, ctx: commands.Context, member: discord.User) -> None:
        """
        The command that adds the specified id to the whitelist of server owners
        """
        if ctx.message.author.id in discord_config['super_admins']:
            await add_to_white_list(member)

    @commands.command(name='update_all_users')
    async def update_all_users(self, ctx: commands.Context) -> None:
        """
        The command that updates the list of users on the server
        """
        for member in ctx.guild.members:
            if member.bot:
                return None

            if member.guild.id != discord_config['server_main']:
                return None

            await self._log(f'New member "{member}" joined')

            with orm.db_session:                            
                if Members.get(id=str(member.id)) is None:
                    await add_user_to_database(member)
                    return None

            await self.__check_status(member)
            await member.add_roles(
                discord.utils.get(
                    member.guild.roles, id=discord_config['role_vi1']
                )
            )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Commands(bot))
    print(f'=== cogs {Commands.__name__} loaded ===')
