import os
import json
import discord
from discord.ext import 

from secret import DISCORD

intents = discord.Intents(members=True, guilds=True, guild_messages=True)
bot = commands.Bot(command_prefix=None, intents=intents)

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        try:
            bot.load_extension(f'cogs.{filename[:-3]}')
        except commands.NoEntryPointError:
            pass

bot.run(DISCORD)
