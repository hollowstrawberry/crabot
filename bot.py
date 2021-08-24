import discord
import re
import json
import os
from discord.ext import commands

prefix = 'grey'
def get_prefix(bot: commands.Bot, message):
    m = re.match(fr'^({prefix}|<@!?{bot.user.id}>) ?', message.content, re.IGNORECASE)
    return m.group() if m else prefix

bot = commands.Bot(command_prefix=get_prefix, description="This is Grey Bot")

with open('bot.config') as f:
    bot.config = json.load(f)


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game('Minecraft'))
    print('Ready')

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cogs.{filename[:-3]}')

bot.run(bot.config['discord'])
