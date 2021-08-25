import os
import re
import json
import hashlib
import aiohttp
import discord
import cv2
from PIL import Image
from discord.ext import commands
from discord.ext.commands import Context
from typing import Union


class Fun(commands.Cog):
    """Commands you might actually want to use"""
    DONUT_FILE = "donuts.json"
    REP_FILE = "reputation.json"
    IMG_DL = "download.png"
    IMG_OUT = "output.jpg"
    donuts = [
        "<:bluedonut:879880267391705089>", "<:plaindonut:879880268431892560>",
        "<:greendonut:879880268482232331>", "<:chocchocdonut:879880268658380840>",
        "<:pinkdonut:879880268704538634>", "<:pinkdonut2:879880268704546826>",
        "<:plaindonutfull:879892288870961262>", "<:whitedonut:879882533553184848>",
        "<:chocdonut:879880269140725800>", "<:chocdonutfull:879892288111783966>",
        "<:whitepinkdonut:879880269434339398>", "<:yellowdonut:879882288270303282>",
        "<:pinkdonutfull:879892287839154268>", "<:chocplaindonut:879880269560152124>",
        "<:whitechocdonut:879880269857976371>", "<:pinkplaindonut:879880269937647616>",
        "<:whitewhitedonut:879892288241815663>", "<:reddonut:879880270105444413>",
        "<:pinkpinkdonut:879880270168330260>", "<:pinkchocdonut:879880271829299220>"]

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['quick,', 'math', 'wolfram'])
    async def quick(self, ctx: Context, *, query: commands.clean_content):
        """Get answers to many questions thanks to WolframAlpha"""
        await ctx.channel.trigger_typing()
        async with aiohttp.ClientSession() as s:
            async with s.get(
                    'https://api.wolframalpha.com/v2/result',
                    params={'i': query, 'appid': self.bot.token['wolfram']}
            ) as res:
                text = await res.text()
                if text == "No short answer available":
                    to_send = "thats too much for my tiny brain"
                elif text == "Wolfram|Alpha did not understand your input":
                    to_send = "nani"
                else:
                    to_send = text
                await ctx.send(to_send)
                print(f"quick {query}")

    @commands.command()
    async def rate(self, ctx: Context, *, thing):
        """Gives a unique rating to anything you want"""
        thing = thing.lower()
        # Invert bot-mention temporarily
        thing = re.sub(f'^<@!?{self.bot.user.id}>$', 'yourself', thing)
        # Capture groups
        author = re.search(r'\b(my|me)\b', thing)
        mention = re.search(r'<@!?([0-9]+)>', thing)
        server = re.search(r'\b(server|guild)\b', thing)
        # Invert mentions temporarily
        thing = re.sub(r"^<@!?[0-9]+> ?'?s\b", 'my', thing)
        thing = re.sub(r'^<@!?[0-9]+>', 'you', thing)
        # Flip grammatical persons
        thing = re.sub(r'\b(me|myself|I)\b', 'you', thing)
        thing = re.sub(r'\byourself\b', 'myself', thing)
        thing = re.sub(r'\byour\b', 'MY', thing)
        thing = re.sub(r'\bmy\b', 'your', thing)
        thing = re.sub(r'MY', 'my', thing)
        # Generate deterministic random value
        formatted = ''.join(ch for ch in thing if ch.isalnum()).encode('utf-8')
        hash = abs(int(hashlib.sha512(formatted).hexdigest(), 16))
        if server:
            hash += ctx.guild.id
        if author:
            hash += ctx.author.id
        elif mention:
            hash += int(mention.group(1))
            thing = re.sub('your', f"{mention.group()}'s", thing)  # Revert mentions
            thing = re.sub('you', mention.group(), thing)
        # Assign score from random value
        if thing.endswith(('ism', 'phobia', 'philia')):
            rating = hash % 3
        elif re.search(r'(orange|food|eat|cry|rights)', thing):
            rating = hash % 4 + 7
        else:
            rating = hash % 11

        await ctx.send(f'I give {thing} a {rating}/10')
        print(f'rate {thing} {rating}')

    @commands.command()
    @commands.cooldown(rate=5, per=5, type=commands.BucketType.channel)
    async def donut(self, ctx: Context):
        """Gives you donuts"""
        try:
            with open(self.DONUT_FILE, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            with open(self.DONUT_FILE, 'w+'):
                data = {}
        count = data.get(str(ctx.author.id), 0) + 1
        data[str(ctx.author.id)] = count
        with open(self.DONUT_FILE, 'w') as file:
            json.dump(data, file)
        hash = abs(int(hashlib.sha256(bytes(count)).hexdigest(), 16)) + 11
        donut = self.donuts[hash % len(self.donuts)]
        await ctx.send(f'{count} {donut}')
        print(f'User {ctx.author.id} now has {count} donuts')

    @commands.command(name="+1", aliases=["rep", "giverep"])
    @commands.cooldown(rate=1, per=3600, type=commands.BucketType.user)
    async def rep(self, ctx: Context, user: discord.User = None):
        """Gives a reputation point, you can give 1 per hour"""
        if not user:
            if ctx.message.reference:
                ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                user = ref.author
            else:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("Reply to a message with this command to give rep, "
                                      "or specify the person manually")
        if user.id == ctx.author.id:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("You can't give rep to yourself dummy")

        try:
            with open(self.REP_FILE, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            with open(self.REP_FILE, 'w+'):
                data = {}
        count = data.get(str(user.id), 0) + 1
        data[str(user.id)] = count
        with open(self.REP_FILE, 'w') as file:
            json.dump(data, file)
        await ctx.send(f'{user.mention} +1 rep!')
        print(f'User {ctx.author.id} now has {count} rep')

    @rep.error
    async def rep_error(self, ctx: Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("You already gave a rep in the last hour!")

    @commands.command(aliases=["paintme", "paint", "drawme"])
    async def draw(self, ctx: Context, user: Union[discord.User, str] = None):
        """Produces a painting of you or someone else"""
        if user == "me" or user is None:
            user = ctx.author
        elif user == "you" or user == "yourself":
            user = self.bot.user
        elif isinstance(user, str):
            return await ctx.send("who?")
        # load image
        await user.avatar_url.save(self.IMG_DL)
        Image.open(self.IMG_DL).convert('RGB').resize((256, 256), Image.BICUBIC).save(self.IMG_OUT)
        img = cv2.imread(self.IMG_OUT, cv2.IMREAD_COLOR)
        # apply morphology open to smooth the outline
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
        morph = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
        # brighten dark regions
        result = cv2.normalize(morph, None, 20, 255, cv2.NORM_MINMAX)
        # save and send
        cv2.imwrite(self.IMG_OUT, result)
        await ctx.send(file=discord.File(self.IMG_OUT))
        # kill
        cv2.destroyAllWindows()
        os.remove(self.IMG_DL)
        os.remove(self.IMG_OUT)
        print(f"Successfully painted user {user.id}")

    @commands.command(aliases=["showrep"])
    async def getrep(self, ctx: Context, user: discord.User = None):
        """Gets the reputation points for a user"""
        if not user:
            user = ctx.author
        try:
            with open(self.REP_FILE, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = {}
        count = data.get(str(user.id), 0)

        embed = discord.Embed(color=int('3B88C3', 16))
        embed.set_author(name=user.display_name, icon_url=str(user.avatar_url))
        numemoji = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
        num = "".join(numemoji[int(d)] for d in str(count))
        embed.description = f'**Reputation points:** {num}'
        await ctx.send(embed=embed)

    @commands.command()
    async def pp(self, ctx: Context):
        """Evaluates your pp"""
        pp = ctx.author.id % 13
        await ctx.send(f'Your pp size is {pp} inches')
        print(f'pp {ctx.author.id} {pp}')

def setup(bot: commands.Bot):
    bot.add_cog(Fun(bot))
