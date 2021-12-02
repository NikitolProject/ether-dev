from pony import orm

from discord.ext import commands, tasks

from . import BasicCog
from .utils import restart_services
from .database import (
    Clans, Guilds, Members,
    RatingClans, TransactionMain,
    MarkGlobal, Ethers, CheckBusy,
    WhiteListUsers
)


class TestDatabase(BasicCog, name="test_database"):

    def __init__(self: "TestDatabase", bot: commands.Bot) -> None:
        """
        Running autotests to check the health of the entire database
        """
        super().__init__(bot)

        self._test_database.start()

    @tasks.loop(minutes=30)
    async def _test_database(self: "TestDatabase") -> None:
        """
        Running autotests to check the health of the entire database
        """
        await self._log(
            "Running autotests to check the health of the entire database"
        )

        try:
            await self._check_members()
            await self._check_guilds()
            await self._check_rating_clans()
            await self._check_transaction_main()
            await self._check_mark_global()
            await self._check_ethers()
            await self._check_check_busy()
            await self._check_white_list_users()
            await self._check_clans()
        except Exception as e:
            await self._fatal(
                f"Autotests failed: {e}"
            )
            restart_services()

    @_test_database.before_loop
    async def before_test_database(self: "TestDatabase") -> None:
        """
        Running autotests to check the health of the entire database
        """
        await self.bot.wait_until_ready()

    async def _check_members(self: "TestDatabase") -> None:
        """
        Checks the members table
        """
        with orm.db_session:
            await self._log("Checking members table")

            for member in orm.select(m for m in Members):
                await self._log(f"Member: {member._id}")

    async def _check_guilds(self: "TestDatabase") -> None:
        """
        Checks the guilds table
        """
        with orm.db_session:
            await self._log("Checking guilds table")

            for guild in orm.select(g for g in Guilds):
                await self._log(f"Guild: {guild._id}")

    async def _check_rating_clans(self: "TestDatabase") -> None:
        """
        Checks the rating clans table
        """
        with orm.db_session:
            await self._log("Checking rating clans table")

            for clan in orm.select(c for c in RatingClans):
                await self._log(f"Clan: {clan._id}")

    async def _check_transaction_main(self: "TestDatabase") -> None:
        """
        Checks the transaction main table
        """
        with orm.db_session:
            await self._log("Checking transaction main table")

            for transaction in orm.select(m for m in TransactionMain):
                await self._log(f"Transaction: {transaction._id}")

    async def _check_mark_global(self: "TestDatabase") -> None:
        """
        Checks the mark global table
        """
        with orm.db_session:
            await self._log("Checking mark global table")

            for mark in orm.select(m for m in MarkGlobal):
                await self._log(f"MarkGlobal: {mark._id}")

    async def _check_ethers(self: "TestDatabase") -> None:
        """
        Checks the ethers table
        """
        with orm.db_session:
            await self._log("Checking ethers table")

            for ether in orm.select(e for e in Ethers):
                await self._log(f"Ether: {ether._id}")

    async def _check_check_busy(self: "TestDatabase") -> None:
        """
        Checks the check busy table
        """
        with orm.db_session:
            await self._log("Checking check busy table")

            for check in orm.select(c for c in CheckBusy):
                await self._log(f"CheckBusy: {check._id}")

    async def _check_white_list_users(self: "TestDatabase") -> None:
        """
        Checks the white list users table
        """
        with orm.db_session:
            await self._log("Checking white list users table")

            for user in orm.select(u for u in WhiteListUsers):
                await self._log(f"WhiteListUsers: {user._id}")

    async def _check_clans(self: "TestDatabase") -> None:
        """
        Checking the clans
        """
        with orm.db_session:
            await self._log(
                "Checking the clans"
            )

            for clan in orm.select(c for c in Clans):
                await self._log(
                    f'Clan "{clan._id}" checked'
                )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(TestDatabase(bot))
    print(f'=== cogs {TestDatabase.__name__} loaded ===')
