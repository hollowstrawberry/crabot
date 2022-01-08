import discord
import asyncio
import random
import re
import aiosqlite as sql
from typing import *
from dataclasses import dataclass
from functools import reduce
from operator import add
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

@dataclass
class UserModel:
    user_id: int
    frequency: int
    model: dict

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
        self.models: Dict[int, UserModel] = {}
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
    async def stats(self, ctx: commands.Context, user: Optional[discord.Member]):
        """Statistics about the simulator, globally or for a user"""
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

        if user:
            if user.id not in self.models:
                await ctx.send("User not found")
                return
            messages = self.models[user.id].frequency
            nodes = count_nodes(self.models[user.id].model)
            words = count_words(self.models[user.id].model)
        else:
            messages = self.message_count
            nodes = reduce(add, [count_nodes(x.model) for x in self.models.values()])
            words = reduce(add, [count_words(x.model) for x in self.models.values()])
        await ctx.send(f"```yaml\nMessages: {messages:,}\nNodes: {nodes:,}\nWords: {words:,}```")

    @simulator.command()
    async def count(self, ctx: commands.Context, user: discord.Member, word):
        """Count instances of a word for a specific user"""
        if user.id not in self.models:
            await ctx.send('User not found')
            return
        occurences = reduce(add, [x.get(word, 0) for x in self.models[user.id].model.values()])
        children = len(self.models[user.id].model.get(word, {}))
        await ctx.send(f"```yaml\nOccurrences: {occurences:,}\nWords that follow: {children:,}```")

    @simulator.command()
    @commands.is_owner()
    async def feed(self, ctx: commands.Context, days: int):
        """Feed past messages into the simulator"""
        await ctx.message.add_reaction(EMOJI_LOADING)
        self.running = False
        self.feeding = True
        self.message_count = 0
        for user in self.models.values():
            user.model = {}
            user.frequency = 0
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
        finally:
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

    def add_message(self, user_id: int, content: str, attachments: List[discord.Attachment] = None) -> bool:
        """Add a message to the model"""
        content = content.replace(CHAIN_END, '') if content else ''
        if attachments and attachments[0].url:
            content += (' ' if content else '') + attachments[0].url
        if not content:
            return False
        tokens = [m.group(1) for m in TOKENIZER.finditer(content)]
        if not tokens:
            return False
        tokens.append(CHAIN_END)
        previous = ""
        self.models.setdefault(int(user_id), UserModel(int(user_id), 0, {}))
        user = self.models[int(user_id)]
        user.frequency += 1
        for token in tokens:
            # Add token or increment its weight by 1
            user.model.setdefault(previous, {})
            user.model[previous][token] = user.model[previous].get(token, 0) + 1
            previous = token
        self.message_count += 1
        return True

    @staticmethod
    async def insert_message_db(message: discord.Message, db: sql.Connection):
        content = message.content
        if message.attachments and message.attachments[0].url:
            content += (' ' if content else '') + message.attachments[0].url
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
                        self.add_message(int(row[0]), row[1])
                        count += 1
            print(f"Model built with {count} messages")
        except Exception as error:
            print(f'Failed to set up crab simulator: {error}')
            await self.output_channel.send(f'Failed to set up: {error}')

    async def run_simulator(self):
        """Run the simulator"""
        self.running = True
        while self.running and not self.feeding:
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

    def generate_message(self) -> (int, str):
        """Generate text based on the models"""
        user_id, = random.choices(population=list(self.models.keys()),
                                  weights=[x.frequency for x in self.models.values()],
                                  k=1)
        result = []
        token = ""
        previous = token
        while token != CHAIN_END:
            token = self.generate_token(self.models[user_id].model, previous)
            result.append(token)
            previous = token
        result = "".join(result[:-1])
        # formatting
        if result.count('(') != result.count(')'):
            result = result.replace('(', '').replace(')', '')
        if result.count('"') % 2 == 1:
            result = result.replace('"', '')
        return user_id, result

    @staticmethod
    def generate_token(model: dict, previous: str) -> str:
        """Where the magic happens"""
        gram, = random.choices(population=list(model[previous].keys()),
                               weights=list(model[previous].values()),
                               k=1)
        return gram

    async def send_generated_message(self):
        user_id, content = self.generate_message()
        user = self.guild.get_member(int(user_id))
        if user is None:
            return
        await self.webhook.send(username=user.display_name,
                                avatar_url=user.avatar_url,
                                content=content,
                                allowed_mentions=discord.AllowedMentions.none())


def setup(bot: commands.Bot):
    bot.add_cog(Simulator(bot))
