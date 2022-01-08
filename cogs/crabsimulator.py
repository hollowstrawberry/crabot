import discord
import asyncio
import random
import json
from typing import List
from discord.ext import commands

GUILD_ID = 756395872811483177
CHANNEL_ID = 929193206472671262
WEBHOOK_NAME = "CrabSimulator"
MESSAGE_CHANCE = 1/7
CONVERSATION_CHANCE = 1/30
CONVERSATION_DELAY = 60
CONVERSATION_MIN = 3
CONVERSATION_MAX = 20

class Crab:
    def __init__(self, user_id: int, phrases: List[str]):
        self.user_id = user_id
        self.phrases = phrases
        self.user: discord.User = None

class Simulator(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.running = False
        self.guild: discord.Guild = None
        self.channel: discord.TextChannel = None
        self.webhook: discord.Webhook = None
        self.crabs: List[Crab] = []
        self.conversation_left = 0
        self.last_phrase: str = ""
        if self.bot.is_ready():
            asyncio.create_task(self.on_ready())

    def cog_unload(self):
        self.running = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.running:
            await self.setup()
            await self.run()

    @commands.command()
    async def crabs(self, ctx: commands.Context):
        """Trigger a crab simulator conversation"""
        for crab in self.crabs:
            if ctx.author.id == crab.user_id:
                self.conversation_left = random.randrange(CONVERSATION_MIN, CONVERSATION_MAX + 1)
                await ctx.message.add_reaction('✅')
                return
        await ctx.message.add_reaction('❌')

    async def setup(self):
        self.guild = self.bot.get_guild(GUILD_ID)
        self.channel = self.guild.get_channel(CHANNEL_ID)
        try:
            # webhook
            webhooks: List[discord.Webhook] = await self.channel.webhooks()
            for webhook in webhooks:
                if webhook.name == WEBHOOK_NAME:
                    self.webhook = webhook
            if self.webhook is None:
                self.webhook = await self.channel.create_webhook(name=WEBHOOK_NAME)
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
            if self.conversation_left:
                if random.random() < MESSAGE_CHANCE:
                    try:
                        await self.send()
                        self.conversation_left -= 1
                    except Exception as error:
                        print(error)
                        try:
                            await self.channel.send(f'Error: {error}')
                        except:
                            pass
                await asyncio.sleep(1)
            else:
                if random.random() < CONVERSATION_CHANCE:
                    self.conversation_left = random.randrange(CONVERSATION_MIN, CONVERSATION_MAX + 1)
                for i in range(CONVERSATION_DELAY):
                    if self.conversation_left or not self.running:
                        break
                    await asyncio.sleep(1)

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
