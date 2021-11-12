import discord

from discord.ext import commands

from . import BasicCog, discord_config
from .utils.messages import add_to_white_list


class Commands(BasicCog, name="commands"):

    @commands.command(name='add_to_white_list')
    async def add_to_white_list(self, ctx: commands.Context, member: discord.User) -> None:
        """
        Команда добавляющая заданный id в whitelist владельцев серверов
        """
        if ctx.message.author.id in discord_config['super_admins']:
            await add_to_white_list(member)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Commands(bot))
    print(f'=== cogs {Commands.__name__} loaded ===')
