from functools import reduce

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
COMMIT_SIZE = 1000
CHAIN_END = "🔚"
CHAIN_SPLIT = "​"
TOKENIZER = re.compile(r"(https?://|(?<=http://)\S+|(?<=https://)\S+|<[@#&!:\w]+\d+>|[\w'-]+|\W+)")
#                        (match URLs but separate the start)        (mentions)      (words)(symbols)

MESSAGE_CHANCE = 1/5
CONVERSATION_CHANCE = 1/30
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
        self.feeding = False
        self.guild: Optional[discord.Guild] = None
        self.input_channel: Optional[discord.TextChannel] = None
        self.output_channel: Optional[discord.TextChannel] = None
        self.role: Optional[discord.Role] = None
        self.webhook: Optional[discord.Webhook] = None
        self.conversation_left = 0
        self.model: dict = {}
        self.message_count = 0
        if self.bot.is_ready():
            asyncio.create_task(self.on_ready())

    def cog_unload(self):
        self.running = False
        self.feeding = False

    @commands.group()
    async def simulator(self, ctx: commands.Context):
        """Commands for the crab conversation simulator"""
        if ctx.invoked_subcommand is None:
            await ctx.send(f"Do `help simulator` for commands")

    @simulator.command()
    async def trigger(self, ctx: commands.Context):
        """Trigger a crab simulator conversation"""
        if self.role not in ctx.author.roles:
            await ctx.message.add_reaction(EMOJI_FAILURE)
            return
        self.start_conversation()
        await ctx.message.add_reaction(EMOJI_SUCCESS)

    @simulator.command()
    async def start(self, ctx: commands.Context):
        """Start the simulator"""
        if self.role not in ctx.author.roles:
            await ctx.message.add_reaction(EMOJI_FAILURE)
            return
        if not self.running and not self.feeding:
            asyncio.create_task(self.run_simulator())
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
    async def stats(self, ctx: commands.Context):
        """Information about the simulator"""
        if self.role not in ctx.author.roles:
            await ctx.message.add_reaction(EMOJI_FAILURE)
            return
        def count_nodes(tree: dict) -> int:
            count = 0
            for node in tree.values():
                if isinstance(node, dict):
                    count += count_nodes(node) + 1
                else:
                    count += 1
            return count
        def count_words(tree: dict) -> int:
            count = 0
            for node in tree.values():
                if isinstance(node, dict):
                    count += count_words(node)
                elif isinstance(node, int):
                    count += node
            return count
        await ctx.send(f"```css\n"
                       f"#Messages: {self.message_count}\n"
                       f"#Nodes: {count_nodes(self.model)}\n"
                       f"#Words: {count_words(self.model)}```")

    @simulator.command()
    async def count(self, ctx: commands.Context, user: discord.Member, word):
        """Count how many children nodes a word has for a specific user"""
        await ctx.send(f"```css\n"
                       f"#Children: {reduce(lambda a, b: a+b, self.model.get(word, {}).values())}\n"
                       f"#Unique: {len(self.model.get(word, {}))}\n```")

    @simulator.command()
    @commands.is_owner()
    async def feed(self, ctx: commands.Context, days: int):
        """Feed past messages into the simulator"""
        await ctx.message.add_reaction(EMOJI_LOADING)
        self.running = False
        self.feeding = True
        try:
            async with sql.connect(DB_FILE) as db:
                await db.execute(f"DELETE FROM {DB_TABLE_MESSAGES}")
                await db.commit()
                start_date = datetime.now() - timedelta(days=days)
                async for message in self.input_channel.history(after=start_date, limit=None):
                    if not self.feeding:
                        break
                    if message.author.bot:
                        continue
                    if self.add_message(message.author.id, message.content, message.attachments):
                        await self.insert_message_db(message, db)
                        if self.message_count % COMMIT_SIZE == 0:
                            await db.commit()
                await db.commit()
        except Exception as error:
            await ctx.send(f"{type(error).__name__}: {error}\n"
                           f"Loaded {self.message_count} messages, "
                           f"{self.message_count // COMMIT_SIZE * COMMIT_SIZE} to database")
        self.feeding = False
        asyncio.create_task(self.run_simulator())
        await ctx.send(f"Loaded {self.message_count} messages")
        await ctx.message.remove_reaction(EMOJI_LOADING, self.bot.user)
        await ctx.message.add_reaction(EMOJI_SUCCESS)

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.running:
            await self.setup_simulator()
            await self.run_simulator()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Processes new incoming messages"""
        if message.channel == self.output_channel and not message.author.bot:
            try:
                await message.delete()
            except:
                pass
            self.start_conversation()
            return
        if message.guild != self.guild or message.channel != self.input_channel:
            return
        if message.author.bot or self.role not in message.author.roles:
            return
        if self.add_message(message.author.id, message.content, message.attachments):
            async with sql.connect(DB_FILE) as db:
                await self.insert_message_db(message, db)
                await db.commit()

    def start_conversation(self):
        self.conversation_left = random.randrange(CONVERSATION_MIN, CONVERSATION_MAX + 1)

    def add_message(self,
                    user_id: Union[str, int],
                    content: str,
                    attachments: List[discord.Attachment] = None) -> bool:
        """Add a message to the model"""
        content = content.replace(CHAIN_SPLIT, '').replace(CHAIN_END, '') if content else ''
        if attachments and attachments[0].url:
            content += (' ' if content else '') + attachments[0].url
        if not content:
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
        self.message_count += 1
        return True

    @staticmethod
    async def insert_message_db(message: discord.Message, db: sql.Connection):
        await db.execute(f'INSERT INTO {DB_TABLE_MESSAGES} VALUES (?, ?);',
                         [str(message.author.id), message.content])

    async def setup_simulator(self):
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
            count = 0
            async with sql.connect(DB_FILE) as db:
                await db.execute(f"CREATE TABLE IF NOT EXISTS {DB_TABLE_MESSAGES} "
                                 f"(user_id TEXT NOT NULL, content TEXT NOT NULL);")
                async with db.execute(f"SELECT * FROM {DB_TABLE_MESSAGES}") as cursor:
                    async for row in cursor:
                        self.add_message(row[0], row[1])
                        count += 1
            print(f"Model built with {count} messages")
        except Exception as error:
            print(f'Failed to set up crab simulator: {error}')
            await self.output_channel.send(f'Failed to set up: {error}')

    async def run_simulator(self):
        """Run the simulator"""
        self.running = True
        while self.running:
            if self.conversation_left:
                if random.random() < MESSAGE_CHANCE:
                    try:
                        self.conversation_left -= 1
                        await self.send_generated_message()
                    except Exception as error:
                        print(f'{type(error).__name__}: {error}')
                        try:
                            await self.output_channel.send(f'{type(error).__name__}: {error}')
                        except:
                            pass
                await asyncio.sleep(1)
            else:
                if random.random() < CONVERSATION_CHANCE:
                    self.start_conversation()
                for i in range(CONVERSATION_DELAY):
                    if self.conversation_left or not self.running:
                        break
                    await asyncio.sleep(1)

    def generate_message(self) -> str:
        """Generate text based on the model"""
        output = []
        token = ""
        previous = token
        while token != CHAIN_END:
            token = self.generate_token(self.model, previous)
            output.append(token)
            previous = token
        result = "".join(output[:-1])
        # formatting
        if result.count('(') > result.count(')'):
            result += ')'
        return result

    @staticmethod
    def generate_token(model: dict, previous: str) -> str:
        """Where the magic happens"""
        gram, = random.choices(population=list(model[previous].keys()),
                               weights=list(model[previous].values()),
                               k=1)
        return gram

    async def send_generated_message(self):
        user_id, phrase = self.generate_message().split(CHAIN_SPLIT)
        try:
            user = self.guild.get_member(int(user_id))
            if user is None: raise ValueError
        except ValueError:
            raise ValueError(f"Can't find user")
        await self.webhook.send(username=user.display_name,
                                avatar_url=user.avatar_url,
                                content=phrase,
                                allowed_mentions=None)


def setup(bot: commands.Bot):
    bot.add_cog(Simulator(bot))
