import discord
import asyncio
import random
import json
import re
from typing import List
from discord.ext import commands

GUILD_ID = 756395872811483177
CHANNEL_ID = 929193206472671262
ROLE_ID = 756398304052641953
WEBHOOK_NAME = "CrabSimulator"
DATABASE = "markov.sqlite"
WORD_TOKENIZER = re.compile(r'\b(<a?:\w+:\d+>|[\w-]+)\b')
MESSAGE_CHANCE = 1/5
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
        self.role: discord.Role = None
        self.webhook: discord.Webhook = None
        self.crabs: List[Crab] = []
        self.conversation_left = 0
        self.chains: dict = {}
        if self.bot.is_ready():
            asyncio.create_task(self.on_ready())

    def cog_unload(self):
        self.running = False

    @commands.group()
    async def simulator(self, ctx: commands.Context):
        """Simulates crab conversations"""
        pass

    @commands.command()
    async def trigger(self, ctx: commands.Context):
        """Trigger a crab simulator conversation"""
        if self.role not in ctx.author.roles:
            await ctx.message.add_reaction('❌')
            return
        self.conversation_left = random.randrange(CONVERSATION_MIN, CONVERSATION_MAX + 1)
        await ctx.message.add_reaction('✅')

    @commands.command()
    async def start(self, ctx: commands.Context):
        """Start the simulator"""
        if self.role not in ctx.author.roles:
            await ctx.message.add_reaction('❌')
            return
        self.running = True
        await ctx.message.add_reaction('✅')

    @commands.command()
    async def stop(self, ctx: commands.Context):
        """Stop the simulator"""
        if self.role not in ctx.author.roles:
            await ctx.message.add_reaction('❌')
            return
        self.running = False
        await ctx.message.add_reaction('✅')

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.running:
            await self.setup()
            await self.run()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Processes new incoming messages"""
        if message.guild != self.guild or message.channel != self.channel or self.role not in message.author.roles:
            return
        if message.author.bot:
            return
        self.add_message(message.author.id, message.content)

    def add_message(self, user_id: int, content: str):
        """Add a message to the model"""
        depth = 1
        model = self.chains.get(depth, {})
        state = str(user_id)  # Begin all state chains with the user marker
        tokens = [m.group(1) for m in WORD_TOKENIZER.finditer(content)]
        for i, token in enumerate(tokens):
            # Ensure dict key for vector distribution is created
            model[state] = model.get(state, {})
            # Increment the weight for this state vector or initialize it to 1
            model[state][token] = model[state].get(token, 0) + 1
            # Produce sliding state window (ngram)
            j = 1 + i - depth if i >= depth else 0
            state = "".join(x for x in tokens[j:i + 1])
        # Store the model
        self.chains[depth] = model

    def generate_text(self, depth: int):
        """Generate text based on the model"""
        try:
            model = self.chains[depth]
        except KeyError:
            return "Error: can't find a model to use"
        output = []
        i = 0
        gram = ""
        state = ""
        while gram != "":
            gram = self.choose_gram(model, state)
            output.append(' ' + gram)
            # Produce sliding state window (ngram)
            i += 1
            j = i - depth if i > depth else 0
            state = "".join(output[j:i])
        if not output:
            return
        return "".join(output[:-1])

    @staticmethod
    def choose_gram(model: dict, state: str):
        """Here lies the secret sauce"""
        gram, = random.choices(population=list(model[state].keys()),
                               weights=list(model[state].values()),
                               k=1)  # Caution: basically magic
        return gram

    async def setup(self):
        """Set up the simulator"""
        self.guild = self.bot.get_guild(GUILD_ID)
        self.channel = self.guild.get_channel(CHANNEL_ID)
        self.role = self.guild.get_role(ROLE_ID)
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
                    crab.user = self.guild.get_member(crab.user_id)
                    if crab.user is not None:
                        self.crabs.append(crab)
                    else:
                        print(f"User {crab.user_id} not found")
        except Exception as error:
            print(f'Failed to set up crab simulator: {error}')
            await self.channel.send(f'Failed to set up: {error}')

    async def run(self):
        """Run the simulator"""
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
        phrase = self.generate_text(1)
        user_id = phrase.split(' ')[0]
        phrase = phrase.removeprefix(user_id + ' ')
        try:
            user = self.guild.get_member(int(user_id))
        except ValueError:
            print(f"Invalid id {user_id} in markov chain")
            return
        if user is None:
            print("Can't find user for simulator")
            return
        await self.webhook.send(username=user.display_name,
                                avatar_url=user.avatar_url,
                                content=phrase)


def setup(bot: commands.Bot):
    bot.add_cog(Simulator(bot))
