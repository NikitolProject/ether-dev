from discord.ext import commands

bot = commands.Bot(command_prefix='!')

bot.remove_command('help')

bot.load_extension('test')
bot.load_extension('tests.test_two.test')

bot.run('OTA1NDUzNzY1Mjc1MDI5NTE0.YYKTiA.Q-2uz-VUH02cH4k8qdoIW5exdYw')
