from discord.ext import commands


class TestOne(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def test_one(self, ctx):
        await ctx.send('test_one')


def setup(bot):
    bot.add_cog(TestOne(bot))
