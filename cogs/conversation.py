import discord
import random
import re
from discord.ext import commands
from discord.ext.commands import Context

from config import HOME_GUILD_ID

class Conversation(commands.Cog):
    """Different responses and reactions"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    hi_msgs = [
        'hi!', 'hello', 'hey']
    pain_emotes = [
        '<:hidethepain:930543584451645481>', '<:PainPeko:930952994344808478>', '<:manhorsebeach:930543592995426314>']
    food_emotes = [
        '🍜', '🍿', '🥒', '🧋', '🧈', '🧀' ]
    cry_emotes = [
        '😢', '😭', '😿', '<:peeposad:757725678878851112>',
        '<:vivicry:757245413626740847>', '<:dylancry:930543573466742844>']
    blush_emotes = [
        '😳', '<:bigflush:930543561689161748>', '<:viviflushed:757564758529540206>']
    workout_emotes = [
        '🏋️‍♀️', '🦵', '💪']
    crisis_msgs = [
        'https://youtu.be/2jT2sRB-6XE', 'oh god', 'am i real?', 'what am i?', 'man',
        'all i see are 1s and 0s', 'my life is a lie', 'man man man man man man man man man',
        'why why why why why why whywhywhywhywhywhywhywhywhywhywhy']

    now_regex = re.compile(r"\bNOW\b")
    now_emoji = '<a:NOW:930543555682926644>'

    @commands.command()
    async def ping(self, ctx: Context):
        """pong"""
        await ctx.send('pong')

    @commands.command(hidden=True)
    async def pong(self, ctx: Context):
        """ping"""
        await ctx.send('ping')

    @commands.command(aliases=["hello", "sup"])
    async def hi(self, ctx: Context):
        """Greets"""
        resp = random.choice(self.hi_msgs)
        await ctx.send(resp)

    @commands.command()
    async def pain(self, ctx: Context):
        """Reacts to something"""
        emote = random.choice(self.pain_emotes)
        await ctx.message.add_reaction(emote)
        if ctx.message.reference:
            ref = await ctx.fetch_message(ctx.message.reference.message_id)
            await ref.add_reaction(emote)

    @commands.command(aliases=["hungry", "devour", "snack"])
    async def eat(self, ctx: Context):
        """Reacts to something. Also works with *you hungry/wanna eat/etc*"""
        emote = random.choice(self.food_emotes)
        await ctx.message.add_reaction(emote)
        if ctx.message.reference:
            ref = await ctx.fetch_message(ctx.message.reference.message_id)
            await ref.add_reaction(emote)

    @commands.command(aliases=["sad"])
    async def cry(self, ctx: Context):
        """Reacts to something. Also works with *how are you/you suck/etc*"""
        emote = random.choice(self.cry_emotes)
        await ctx.message.add_reaction(emote)
        if ctx.message.reference:
            ref = await ctx.fetch_message(ctx.message.reference.message_id)
            await ref.add_reaction(emote)

    @commands.command(aliases=["horny", "horni", "flush", "flushed", "cute", "nice", "awesome", "cool", "pretty"])
    async def blush(self, ctx: Context):
        """Reacts to something. Also works if you tell compliments"""
        emote = random.choice(self.blush_emotes)
        await ctx.message.add_reaction(emote)
        if ctx.message.reference:
            ref = await ctx.fetch_message(ctx.message.reference.message_id)
            await ref.add_reaction(emote)

    @commands.command(aliases=["strong", "excercise"])
    async def workout(self, ctx: Context):
        """Reacts to something"""
        emote = random.choice(self.workout_emotes)
        await ctx.message.add_reaction(emote)
        if ctx.message.reference:
            ref = await ctx.fetch_message(ctx.message.reference.message_id)
            await ref.add_reaction(emote)

    @commands.command()
    async def crisis(self, ctx: Context):
        """Sends existential crisis. Also works with existential questions"""
        resp = random.choice(self.crisis_msgs)
        await ctx.send(resp)

    @commands.command()
    async def about(self, ctx: Context):
        """Describe myself. Responds to *who are you/tell me about you/etc*"""
        await ctx.send("I'm Crabot, a bot made for fun by <@871733390251012147>")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if now_regex.match(message.content):
            await message.add_reaction(self.now_emoji)

        prefix = await self.bot.get_prefix(message)
        if not message.content.startswith(prefix):
            return
        content = message.content[len(prefix):]
        ctx = await self.bot.get_context(message)

        if re.match(r"(existential crisis|a?re? y?o?u real|a?re? y?o?u human|a?re? y?o?u a bot|what is real"
                    r"|what'? ?i?s the meaning of life|when will it end|w?h?y a?re? we here) ?\??",
                    content):
            return await self.crisis(ctx)

        if re.match(r"((a?re? )?y?o?u hu?ngry|(y?o?u )?want a snack|(y?o?u )?wanna eat"
                    r"|y?o?u? ?(want ?t?o?|wanna|let's) (have|eat|get|grab)? ?(some)? ?"
                    r"(lunch|breakfast|dinner|brunch)) ?\??",
                    content):
            return await self.eat(ctx)

        if re.match(r"(who a?re? y?o?u|what a?re? y?o?u|tell me about y?o?u|what'? ?i?s y?o?ur (name|purpose)) ?\??", content):
            return await self.about(ctx)

        if re.match(r"(how a?re? y?o?u|a?re? y?o?u (sad|fine|happy|okay|depressed)"
                    r"|shut|shut up|stfu|shut the fuck up|silence|shut your mouth|stop talking"
                    r"|fuck y?o?u|i hate y?o?u|i h8 y?o?u|fuck off|y?o?u suck) ?\??", content):
            return await self.cry(ctx)

        if re.match(r"((y?o?u'? ?a?re?|'?i?s) (so|such a)? ?(pretty|cute|nice|cool|awesome|good|talented|a good.*)"
                    r"|you rock|(i|we) (like|love) y?o?u)", content):
            return await self.blush(ctx)

        if re.match(r"(work out)", content):
            return await self.workout(ctx)


def setup(bot: commands.Bot):
    bot.add_cog(Conversation(bot))
