import discord
import asyncio
import random
import json
from typing import List
from discord.ext import commands

class Crab:
    def __init__(self, user_id: int, phrases: List[str]):
        self.user_id = user_id
        self.phrases = phrases
        self.user: discord.User = None

class Simulator(commands.Cog):
    GUILD_ID = 756395872811483177
    CHANNEL_ID = 929193206472671262
    WEBHOOK_NAME = "CrabSimulator"

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.running = False
        self.guild: discord.Guild = None
        self.channel: discord.TextChannel = None
        self.webhook: discord.Webhook = None
        self.crabs: List[Crab] = []
        self.last_phrase: str = ""

    @commands.command()
    @commands.is_owner()
    async def startsimulator(self, ctx):
        await self.on_ready()

    def cog_unload(self):
        self.running = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.running:
            await self.setup()
            await self.run()

    async def setup(self):
        self.guild = self.bot.get_guild(self.GUILD_ID)
        self.channel = self.guild.get_channel(self.CHANNEL_ID)
        try:
            # webhook
            webhooks: List[discord.Webhook] = await self.channel.webhooks()
            for webhook in webhooks:
                if webhook.name == self.WEBHOOK_NAME:
                    self.webhook = webhook
            if self.webhook is None:
                self.webhook = await self.channel.create_webhook(name=self.WEBHOOK_NAME)

            # users
            with open('crabs.json') as f:
                data: dict = json.load(f)
                for key, val in data.items():
                    if val is None:
                        continue
                    crab = Crab(int(key), val)
                    crab.user = await self.guild.fetch_member(crab.user_id)
                    self.crabs.append(crab)
        except Exception as error:
            print(f'Failed to set up crab simulator: {error}')
            await self.channel.send(f'Failed to set up: {error}')

    async def run(self):
        self.running = True
        while self.running:
            await asyncio.sleep(1)
            if random.randint(0, 10) == 0:
                try:
                    await self.send()
                except Exception as error:
                    print(error)
                    try:
                        await self.channel.send(f'Error: {error}')
                    except:
                        pass

    async def send(self):
        crab = random.choice(self.crabs)
        phrase = self.last_phrase
        while phrase == self.last_phrase:
            phrase = random.choice(crab.phrases)
        self.last_phrase = phrase
        await self.webhook.send(username=crab.user.display_name,
                                avatar_url=crab.user.avatar_url,
                                content=phrase)


def setup(bot: commands.Bot):
    bot.add_cog(Simulator(bot))
