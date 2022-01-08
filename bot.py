import discord
import re
import json
import os
from discord.ext import commands

prefix = 'smoke'
def get_prefix(bot: commands.Bot, message):
    m = re.match(fr'^({prefix}|<@!?{bot.user.id}>) ?,? ?', message.content, re.IGNORECASE)
    return m.group() if m else prefix

bot = commands.Bot(command_prefix=get_prefix, activity=discord.Game('Minecraft'))

with open('token.json') as f:
    bot.token = json.load(f)

@bot.event
async def on_ready():
    print('Ready')

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        try:
            bot.load_extension(f'cogs.{filename[:-3]}')
        except commands.NoEntryPointError:
            pass

bot.run(bot.token['discord'])
