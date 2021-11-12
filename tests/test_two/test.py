from discord.ext import commands


class TestTwo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def test_two(self, ctx):
        await ctx.send('test_two')


def setup(bot):
    bot.add_cog(TestTwo(bot))
