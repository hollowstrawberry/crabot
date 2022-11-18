import os
import discord
import asyncio
from discord.ext import commands

import secret

bot = commands.Bot(command_prefix=None, intents=discord.Intents.all())

async def main():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
            except commands.NoEntryPointError:
                pass
    await bot.start(secret.DISCORD)

if __name__ == "__main__":
    asyncio.run(main())
