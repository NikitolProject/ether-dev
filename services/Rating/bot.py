import os

import discord

from dotenv import load_dotenv

from discord.ext import commands

from src.utils import *

load_dotenv('.env')

activity = discord.Activity(type=discord.ActivityType.listening, name="discord.gg/ethercity")
bot = commands.Bot(command_prefix='___', intents=discord.Intents.all(), activity=activity, status=discord.Status.idle)
bot.remove_command('help')

bot.load_extension('src.events')

bot.run(os.environ['DISCORD_BOT_TOKEN'])
