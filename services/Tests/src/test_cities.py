import discord

from datetime import datetime

from pony import orm

from discord_components import Button, ButtonStyle
from discord.ext import commands, tasks

from . import BasicCog
from .database import (
    Clans, Guilds, TransactionMain
)


class TestCities(BasicCog, name="test_cities"):

    def __init__(self: "TestCities", bot: commands.Bot) -> None:
        super().__init__(bot)

        self._test_cities.start()

    @tasks.loop(minutes=1)
    async def _test_cities(self: "TestCities") -> None:
        """
        Checking all cities
        """
        with orm.db_session:
            guilds: Guilds = Guilds.select()
            
            if not guilds.exists():
                return None

            for guild in guilds:
                await self.__check_city(guild)

    @_test_cities.before_loop
    async def before_test_cities(self: "TestCities") -> None:
        """
        Start checking all cities
        """
        await self._log(
            "Start checking all cities"
        )

        await self.bot.wait_until_ready()

    async def __check_city(self: "TestCities", city: Guilds) -> None:
        """
        Checking a specific city
        """
        guild: discord.Guild = self.bot.get_guild(int(city.id))
        bot: discord.Member = guild.get_member(self.bot.user.id)

        bot_role_position: int = -1
        for role in guild.roles:
            if role.name == bot.roles[1].name:
                bot_role_position = 0
                continue

            if not str(role.id) in [city.role_ether, city.role_nods]:
                continue

            if bot_role_position == -1:
                continue

            return await self.__froze_city(city)
        await self._log(
            f"City {guild.name} has been checked"
        )

    async def __froze_city(self: "TestCities", guild: Guilds) -> None:
        """
        Frozing a city
        """
        with orm.db_session:
            await self._log(
                f"Frozing a city {guild.name}"
            )

            if guild.frozen:
                return None

            guild.frozen = True
            Clans.get(guild=str(guild.id)).frozen = True

            TransactionMain(
                type="frost_guild",
                date=datetime.now(),
                guild=str(guild.id),
                owner=str(guild.owner_id),
                clans=guild.clans
            )

            orm.commit()

            owner: discord.Member = self.bot.get_user(int(guild.owner_id))
            await owner.send(
                embed=discord.Embed(
                    title=  "Your city is frozen",
                    description="To defrost the city, click on the button below",
                    color=discord.Color.red(),
                ),
                components=[
                    [
                        Button(
                            style=ButtonStyle.green,
                            label="Defrost the city"
                        )
                    ]
                ]
            )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(TestCities(bot))
    print(f'=== cogs {TestCities.__name__} loaded ===')
