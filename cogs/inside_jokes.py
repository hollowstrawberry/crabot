import discord
import asyncio
from datetime import datetime, timedelta
from discord.ext import commands
from typing import *
from config import HOME_GUILD_ID

HOME_CHANNEL_ID = 930471825668988959
FOURTWENTY_GUILD_ID = 755538135491805305
FOURTWENTY_CHANNEL_ID = 760037213702193152

class InsideJokes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.running = False
        self.fourtwenty: Optional[discord.Channel] = None
        self.home: Optional[discord.Guild] = None
        self.sentwarn = []
        if self.bot.is_ready():
            asyncio.create_task(self.on_ready())

    def cog_unload(self):
        self.running = False

    @commands.Cog.listener()
    async def on_ready(self):
        self.fourtwenty = self.bot.get_guild(FOURTWENTY_GUILD_ID).get_channel(FOURTWENTY_CHANNEL_ID)
        self.home = self.bot.get_guild(HOME_GUILD_ID)
        self.home_channel = self.home.get_channel(HOME_CHANNEL_ID)
        if not self.running:
            await self.run()

    async def run(self):
        while self.running:
            now = datetime.now()

            if now.hour+3 == 4 and now.minute == 20:
                try:
                    await self.fourtwenty.send("420")
                except Exception as error:
                    print(error)

            for user in self.home.members:
                if user.activity and user.activity.name == 'League of Legends' and user.activity.created_at:
                    if user.id not in self.sentwarn and now - user.activity.created_at > timedelta.min(30):
                        try:
                            await self.home_channel.send(f'{user.mention} stop playing league of legends stinky')
                        except Exception as error:
                            print(error)
                        self.sentwarn.append(user.id)
                elif user.id in self.sentwarn:
                    self.sentwarn.remove(user.id)

            await asyncio.sleep(30)

def setup(bot: commands.Bot):
    bot.add_cog(InsideJokes(bot))
