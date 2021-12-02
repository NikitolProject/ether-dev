import asyncio
import aiohttp

import contextlib

import discord

from captcha.image import ImageCaptcha
from discord import colour
from discord.channel import DMChannel
from discord_components import DiscordComponents, component
from discord.ext import commands

from . import BasicCog, discord_config
from .utils import *
from .database import (
    Clans, Guilds, Members,
    RatingClans
)


class Security(BasicCog, name="security"):

    @commands.Cog.listener()
    async def on_ready(self: "Security") -> None:
        """
        The main event that displays the bot's readiness to work
        """
        if not discord_config['security']:
            embed = discord.Embed(
                title="Security check",
                description="Please click on the button to enter the captcha further.",
                color=discord.Color.dark_blue()
            )
            await self.bot.get_channel(ether_city_channels['validate']).send(
                embed=embed,
                components=[
                    [
                        Button(style=ButtonStyle.blue, label='Enter a captcha')
                    ]
                ]
            )

    async def send_captcha(self: "Security", interaction: Interaction) -> None:
        """
        Sending captcha to the user
        """
        await self._log(f'Sending captcha to {interaction.author.display_name}')

        image = ImageCaptcha(width=280, height=90)

        async with aiohttp.ClientSession() as session:
            async with session.get(
                'https://www.random.org/strings/?num=1&len=6&digits'
                '=on&upperalpha=on&loweralpha=on&unique=on&format=p'
                'lain&rnd=new'
            ) as response:
                captcha_text = await response.text()

        captcha_text = captcha_text.replace("\n", "")

        image.write(captcha_text, f'captcha_{interaction.author.id}.png')

        dm: DMChannel = await interaction.author.create_dm()

        await interaction.respond(
            embed=discord.Embed(
                description=f"Please go to the [bot's private messages](https://discord.com/channels/@me/{dm.id})",
                color=discord.Colour.dark_blue()
            )
        )

        file=discord.File(f'captcha_{interaction.author.id}.png')

        embed = discord.Embed(
            title="Enter the captcha from the image",
            colour=INVISIBLE_COLOR
        )

        embed.set_image(url=f'attachment://captcha_{interaction.author.id}.png')

        await interaction.author.send(
            embed=embed, file=file
        )

        while True:
            try:
                message = await self.bot.wait_for(
                    'message', timeout=120,
                    check=lambda m: m.author == interaction.user and m.channel.type == discord.ChannelType.private
                )

                if message.content.lower() == captcha_text.lower():
                    await interaction.author.send(
                        embed=discord.Embed(
                            title="Captcha success",
                            description="You have successfully passed the captcha.",
                            colour=discord.Color.green()
                        )
                    )

                    await self.__on_member_join(interaction.author)
                    return None
                
                await interaction.author.send(
                    embed=discord.Embed(
                        title="Wrong captcha",
                        description="Please try again.",
                        colour=discord.Color.dark_red()
                    )
                )

            except asyncio.TimeoutError:
                await interaction.author.send(
                    embed=discord.Embed(
                        title="Captcha expired",
                        description="Please try again.",
                        colour=discord.Color.dark_red()
                    )
                )
                return None

    async def __on_member_join(self: "Security", member: discord.Member) -> None:
        """
        The event that displays the new member
        """
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
    
    async def __check_status(self: "Security", member: discord.Member) -> None:
        """
        Checking all kinds of user awards
        """
        await self._log(
            f'Checking status for member: {member.id}'
        )

        guild: discord.Guild = member.guild
    
        with orm.db_session:
            m_guild: Guilds = Guilds.get(id=str(guild.id))
        
            with contextlib.suppress(Exception):
                if not Members.get(id=str(member.id)).ether_status and \
                    not Members.get(id=str(member.id)).nods_status:
                    return None
                
                if m_guild.role_ether is None and m_guild.role_nods is None:
                    return None

                if guild.get_role(int(m_guild.role_ether)) is None and \
                    guild.get_role(int(m_guild.role_nods)) is None:
                    return None

                await member.add_roles(
                    guild.get_role(int(m_guild.role_ether)) if \
                        Members.get(id=str(member.id)).ether_status else None,
                    guild.get_role(int(m_guild.role_nods)) if \
                        Members.get(id=str(member.id)).nods_status else None
                )
                await asyncio.sleep(0.1)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Security(bot))
    print(f'=== cogs {Security.__name__} loaded ===')
