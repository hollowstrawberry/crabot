import discord
import asyncio
import random
import re
import aiosqlite as sql
from typing import *
from datetime import datetime, timedelta
from discord.ext import commands

GUILD_ID = 756395872811483177
INPUT_CHANNEL_ID = 756409304894144575
OUTPUT_CHANNEL_ID = 929193206472671262
ROLE_ID = 756398304052641953
WEBHOOK_NAME = "CrabSimulator"

DB_FILE = "markov.sqlite"
DB_TABLE_MESSAGES = "messages"
COMMIT_SIZE = 100
CHAIN_END = "🔚"
CHAIN_SPLIT = "​"
TOKENIZER = re.compile(r'(\w+|\W+)')

MESSAGE_CHANCE = 1/5
CONVERSATION_CHANCE = 1/20
CONVERSATION_DELAY = 60
CONVERSATION_MIN = 4
CONVERSATION_MAX = 15

EMOJI_LOADING = '<a:loading:410612084527595520>'
EMOJI_SUCCESS = '✅'
EMOJI_FAILURE = '❌'

class Simulator(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.running = False
        self.guild: Optional[discord.Guild] = None
        self.input_channel: Optional[discord.TextChannel] = None
        self.output_channel: Optional[discord.TextChannel] = None
        self.role: Optional[discord.Role] = None
        self.webhook: Optional[discord.Webhook] = None
        self.conversation_left = 0
        self.model: dict = {}
        if self.bot.is_ready():
            asyncio.create_task(self.on_ready())

    def cog_unload(self):
        self.running = False

    @commands.group()
    async def simulator(self, ctx: commands.Context):
        """Simulates crab conversations"""
        pass

    @simulator.command()
    async def trigger(self, ctx: commands.Context):
        """Trigger a crab simulator conversation"""
        if self.role not in ctx.author.roles:
            await ctx.message.add_reaction(EMOJI_FAILURE)
            return
        self.conversation_left = random.randrange(CONVERSATION_MIN, CONVERSATION_MAX + 1)
        await ctx.message.add_reaction(EMOJI_SUCCESS)

    @simulator.command()
    async def start(self, ctx: commands.Context):
        """Start the simulator"""
        if self.role not in ctx.author.roles:
            await ctx.message.add_reaction(EMOJI_FAILURE)
            return
        self.running = True
        await ctx.message.add_reaction(EMOJI_SUCCESS)

    @simulator.command()
    async def stop(self, ctx: commands.Context):
        """Stop the simulator"""
        if self.role not in ctx.author.roles:
            await ctx.message.add_reaction(EMOJI_FAILURE)
            return
        self.running = False
        await ctx.message.add_reaction(EMOJI_SUCCESS)

    @simulator.command()
    @commands.is_owner()
    async def feed(self, ctx: commands.Context, days: int):
        """Feed past messages into the simulator"""
        await ctx.message.add_reaction(EMOJI_LOADING)
        count = 0
        try:
            async with sql.connect(DB_FILE) as db:
                await db.execute(f"DELETE FROM {DB_TABLE_MESSAGES}")
                await db.commit()
                start_date = datetime.now() - timedelta(days=days)
                async for message in self.input_channel.history(after=start_date, limit=None):
                    if self.add_message(message.author.id, message.content):
                        await self.insert_message_db(message, db)
                        count += 1
                        if count % COMMIT_SIZE == 0:
                            await db.commit()
                await db.commit()
        except Exception as error:
            await ctx.send(f"{type(error).__name__}: {error}\n"
                           f"Loaded {count} messages, {count // COMMIT_SIZE * COMMIT_SIZE} to database")
        await ctx.send(f"Loaded {count} messages")
        await ctx.message.remove_reaction(EMOJI_LOADING, self.bot.user)
        await ctx.message.add_reaction(EMOJI_SUCCESS)

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.running:
            await self.setup()
            print(self.model)
            await self.run()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Processes new incoming messages"""
        if message.guild != self.guild or message.channel != self.input_channel:
            return
        if self.role not in message.author.roles or message.author.bot:
            return
        if self.add_message(message.author.id, message.content):
            async with sql.connect(DB_FILE) as db:
                await self.insert_message_db(message, db)
                await db.commit()

    def add_message(self, user_id: Union[str, int], content: str) -> bool:
        """Add a message to the model"""
        if content is None:
            return False
        content = content.replace(CHAIN_SPLIT, '').replace(CHAIN_END, '')
        if len(content) < 1:
            return False
        tokens = [m.group(1) for m in TOKENIZER.finditer(content)]
        if not tokens:
            return False
        tokens.insert(0, f"{user_id}{CHAIN_SPLIT}")
        tokens.append(CHAIN_END)
        previous = ""
        for token in tokens:
            # Add token or increment its weight by 1
            self.model.setdefault(previous, {})
            self.model[previous][token] = self.model[previous].get(token, 0) + 1
            previous = token
        return True

    @staticmethod
    async def insert_message_db(message: discord.Message, db: sql.Connection):
        await db.execute(f'INSERT INTO {DB_TABLE_MESSAGES} VALUES (?, ?);',
                         [str(message.author.id), message.content])

    async def setup(self):
        """Set up the simulator"""
        try:
            # discord entities
            self.guild = self.bot.get_guild(GUILD_ID)
            self.role = self.guild.get_role(ROLE_ID)
            self.input_channel = self.guild.get_channel(INPUT_CHANNEL_ID)
            self.output_channel = self.guild.get_channel(OUTPUT_CHANNEL_ID)
            if self.guild is None: raise KeyError(self.guild.__name__)
            if self.role is None: raise KeyError(self.role.__name__)
            if self.input_channel is None: raise KeyError(self.input_channel.__name__)
            if self.output_channel is None: raise KeyError(self.output_channel.__name__)
            webhooks = await self.output_channel.webhooks()
            webhooks = [w for w in webhooks if w.user == self.bot.user and w.name == WEBHOOK_NAME]
            self.webhook = webhooks[0] if webhooks else await self.output_channel.create_webhook(name=WEBHOOK_NAME)
            # database
            async with sql.connect(DB_FILE) as db:
                await db.execute(f"CREATE TABLE IF NOT EXISTS {DB_TABLE_MESSAGES} "
                                 f"(user_id TEXT NOT NULL, content TEXT NOT NULL);")
                async with db.execute(f"SELECT * FROM {DB_TABLE_MESSAGES}") as cursor:
                    async for row in cursor:
                        self.add_message(row[0], row[1])
        except Exception as error:
            print(f'Failed to set up crab simulator: {error}')
            await self.output_channel.send(f'Failed to set up: {error}')

    async def run(self):
        """Run the simulator"""
        self.running = True
        while self.running:
            if self.conversation_left:
                if random.random() < MESSAGE_CHANCE:
                    try:
                        self.conversation_left -= 1
                        await self.send()
                    except Exception as error:
                        print(f'{type(error).__name__}: {error}')
                        try:
                            await self.output_channel.send(f'{type(error).__name__}: {error}')
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

    def generate_text(self):
        """Generate text based on the model"""
        output = []
        gram = ""
        previous = gram
        while gram != CHAIN_END:
            gram = self.choose_gram(self.model, previous)
            output.append(gram)
            previous = gram
        return "".join(output[:-1])

    @staticmethod
    def choose_gram(model: dict, previous: str):
        """Where the magic happens"""
        gram, = random.choices(population=list(model[previous].keys()),
                               weights=list(model[previous].values()),
                               k=1)
        return gram

    async def send(self):
        user_id, phrase = self.generate_text().split(CHAIN_SPLIT)
        try:
            user = self.guild.get_member(int(user_id))
        except ValueError:
            raise ValueError(f"Invalid id {user_id} in markov chain")
        if user is None:
            raise KeyError("Can't find user for simulator")
        await self.webhook.send(username=user.display_name,
                                avatar_url=user.avatar_url,
                                content=phrase,
                                allowed_mentions=None)


def setup(bot: commands.Bot):
    bot.add_cog(Simulator(bot))
