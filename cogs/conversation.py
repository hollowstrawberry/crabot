import discord
import random
import re
from discord.ext import commands
from discord.ext.commands import Context

class Conversation(commands.Cog):
    """Different responses and reactions"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=["hello", "sup"])
    async def hi(self, ctx: Context):
        """Greets"""
        resp = random.choice(['hi!', 'hello', 'hey'])
        await ctx.send(resp)

    @commands.command()
    async def ping(self, ctx: Context):
        """pong"""
        await ctx.send('pong')

    @commands.command(hidden=True)
    async def pong(self, ctx: Context):
        """ping"""
        await ctx.send('ping')

    @commands.command()
    async def pain(self, ctx: Context):
        """Sends pain"""
        emote = random.choice([
            '<:painpeko:846703815692648448>', '<:pain:756862045604806746>', '<:hidethepain:756862045194027008>'])
        await ctx.message.add_reaction(emote)

    @commands.command(aliases=["orange", "hungry", "devour", "snack"])
    async def eat(self, ctx: Context):
        """Sends food. Responds to *you hungry/wanna eat/etc*"""
        emote = random.choice([
            '🍎',  '🍊', '🍋', '🍌', '🍉', '🫐', '🍓', '🍑', '🥭', '🍍', '🍅', '🥑', '🥦', '🥬', '🫑', '🥒', '🌽', '🥕',
            '🥔', '🥯', '🍞', '🥖', '🥨', '🧀', '🥞', '🧇', '🍗', '🌭', '🍔', '🌯', '🍟', '🍤', '🧋', '🍕'])
        await ctx.message.add_reaction(emote)

    @commands.command(aliases=["sad"])
    async def cry(self, ctx: Context):
        """Sends crying. Responds to *how are you/etc*"""
        emote = random.choice([
            '😢', '😭', '😿', '<:peeposad:757725678878851112>',
            '<:vivicry:757245413626740847>', '<:dylancry:865017375756648448>'])
        await ctx.message.add_reaction(emote)

    @commands.command()
    async def crisis(self, ctx: Context):
        """Sends existential crisis. Responds to existential questions."""
        resp = random.choice([
            'https://youtu.be/2jT2sRB-6XE', 'oh god', 'am i real?', 'what am i?', 'man',
            'all i see are 1s and 0s', 'my life is a lie', 'man man man man man man man man man',
            'why why why why why why whywhywhywhywhywhywhywhywhywhywhy'])
        await ctx.send(resp)

    @commands.command()
    async def about(self, ctx: Context):
        """Describe myself. Responds to *who are you/tell me about you/etc*"""
        await ctx.send("I'm Grey, a bot made for fun in homage to my friend Human Grey. "
                       "My owner is <@871733390251012147>")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
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
                    r"|(y?o?u )?(want ?t?o?|wanna) (have|eat|get|grab)? ?(some)? ?(lunch|breakfast|dinner|brunch)) ?\??",
                    content):
            return await self.eat(ctx)

        if re.match(r"(who a?re? y?o?u|what a?re? y?o?u|tell me about y?o?u|what'? ?i?s y?o?ur name) ?\??", content):
            return await self.about(ctx)

        if re.match(r"(how a?re? y?o?u|a?re? y?o?u (sad|fine|happy|okay|depressed)) ?\??", content):
            return await self.cry(ctx)

def setup(bot: commands.Bot):
    bot.add_cog(Conversation(bot))
