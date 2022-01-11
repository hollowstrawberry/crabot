import discord
import re
import json
import os
from discord.ext import commands

DEFAULTPREFIX = '%'

def get_prefix(bot: commands.Bot, message):
    try:
        return m.group() if (m := bot.prefix.match(message.content)) else DEFAULTPREFIX
    except Exception:
        return DEFAULTPREFIX

intents = discord.Intents(members=True, guilds=True, guild_messages=True)
bot = commands.Bot(command_prefix=get_prefix, activity=discord.Game('Minecraft'), intents=intents)

with open('token.json') as f:
    bot.token = json.load(f)

@bot.event
async def on_ready():
    bot.prefix = re.compile(fr'^({DEFAULTPREFIX}|crab(ot)?|<@!?{bot.user.id}>),? ?', re.IGNORECASE)
    print('Ready')

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        try:
            bot.load_extension(f'cogs.{filename[:-3]}')
        except commands.NoEntryPointError:
            pass

bot.run(bot.token['discord'])
