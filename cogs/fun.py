import os
import io
import re
import json
import hashlib
import aiohttp
import async_cse
import discord
import cv2
import async_google_trans_new as googletrans
from PIL import Image
from discord.ext import commands
from typing import *

import secret

DONUT_FILE = "donuts.json"
REP_FILE = "reputation.json"
IMG_DL = "download.png"
IMG_OUT = "output.jpg"

DONUTS = [
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


class Fun(commands.Cog):
    """Commands you might actually want to use"""
    def __init__(self, bot):
        self.bot = bot
        self.google = async_cse.Search(secret.GOOGLE)
        self.translator = googletrans.AsyncTranslator()

    @commands.command(aliases=['quick,', 'math', 'wolfram'])
    async def quick(self, ctx: commands.Context, *, query: commands.clean_content):
        """Get answers to many questions thanks to WolframAlpha"""
        await ctx.channel.trigger_typing()
        async with aiohttp.ClientSession() as s:
            async with s.get(
                    'https://api.wolframalpha.com/v2/result',
                    params={'i': query, 'appid': secret.WOLFRAM}
            ) as res:
                text = await res.text()
                if text == "No short answer available":
                    to_send = "<a:vibebones:756859685281202186>"
                elif text == "Wolfram|Alpha did not understand your input":
                    to_send = "I have no idea what you're asking but the answer is yes"
                else:
                    to_send = text
                await ctx.send(to_send)
                print(f"quick {query}")

    @commands.command()
    async def define(self, ctx: commands.Context, *, query: commands.clean_content):
        """Get a word definition thanks to WolframAlpha"""
        await self.quick(ctx, query=f"define {query}")

    @commands.command(aliases=['search'])
    async def google(self, ctx: commands.Context, *, query: commands.clean_content):
        """Search something on Google"""
        await ctx.channel.trigger_typing()
        try:
            result = await self.google.search(str(query), safesearch=not ctx.channel.nsfw)
        except Exception as error:
            await ctx.send(f"{type(error).__name__}: {error}")
            return
        if not result or not result[0]:
            await ctx.send("No results")
            return
        embed = discord.Embed(title=result[0].title[:255], description=result[0].description[:1990],
                              url=result[0].url, color=0xffffff)
        if result[0].image_url:
            embed.set_thumbnail(url=result[0].image_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def translate(self, ctx: commands.Context, *, query: commands.clean_content):
        try:
            result = await self.translator.translate(query, "en")
            if not result:
                raise Exception()
        except Exception:
            await ctx.send("Failed to translate, sorry.")
        ctx.send(result)

    @commands.command()
    async def rate(self, ctx: commands.Context, *, thing):
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
        hashed = abs(int(hashlib.sha512(formatted).hexdigest(), 16))
        if server:
            hashed += ctx.guild.id
        if author:
            hashed += ctx.author.id
        elif mention:
            hashed += int(mention.group(1))
            thing = re.sub('your', f"{mention.group()}'s", thing)  # Revert mentions
            thing = re.sub('you', mention.group(), thing)
        # Assign score from random value
        if thing.endswith(('ism', 'phobia', 'philia')):
            rating = hashed % 3
        elif re.search(r'(orange|food|eat|cry|rights)', thing):
            rating = hashed % 4 + 7
        else:
            rating = hashed % 11

        await ctx.send(f'I give {thing} a {rating}/10')
        print(f'rate {thing} {rating}')

    @commands.command()
    @commands.cooldown(rate=5, per=5, type=commands.BucketType.channel)
    async def donut(self, ctx: commands.Context):
        """Gives you donuts"""
        try:
            with open(DONUT_FILE, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            with open(DONUT_FILE, 'w+'):
                data = {}
        count = data.get(str(ctx.author.id), 0) + 1
        data[str(ctx.author.id)] = count
        with open(DONUT_FILE, 'w') as file:
            json.dump(data, file)
        hashed = abs(int(hashlib.sha256(bytes(count)).hexdigest(), 16)) + 11
        donut = DONUTS[hashed % len(DONUTS)]
        await ctx.send(f'{count} {donut}')
        print(f'User {ctx.author.id} now has {count} donuts')

    @staticmethod
    async def get_emojis(ctx: commands.Context) -> Optional[List[Tuple[str]]]:
        reference = ctx.message.reference
        if not reference:
            await ctx.send("Reply to a message with this command to steal an emoji")
            return
        message = reference.cached_message or await ctx.channel.fetch_message(reference.message_id)
        if not message:
            await ctx.send("I couldn't grab that message, sorry")
            return
        emojis = re.findall(r"<(a?):(\w+):(\d{10,20})>", message.content)
        if not emojis:
            await ctx.send("Can't find an emoji in that message")
            return
        return emojis

    @commands.group()
    async def steal(self, ctx: commands.Context):
        """Steals emojis you reply to"""
        if ctx.invoked_subcommand:
            return
        if not (emojis := await self.get_emojis(ctx)):
            return
        links = [f"https://cdn.discordapp.com/emojis/{m[2]}.{'gif' if m[0] else 'png'}" for m in emojis]
        await ctx.send('\n'.join(links))

    @steal.command()
    async def upload(self, ctx: commands.Context):
        """Steals emojis you reply to, and uploads it to the server"""
        if not ctx.message.author.guild_permissions.manage_emojis:
            await ctx.send("You don't have permission to manage emojis")
            return
        if not (emojis := await self.get_emojis(ctx)):
            return
        async with aiohttp.ClientSession() as session:
            for emoji in emojis:
                link = f"https://cdn.discordapp.com/emojis/{emoji[2]}.{'gif' if emoji[0] else 'png'}"
                try:
                    async with session.get(link) as resp:
                        image = io.BytesIO(await resp.read()).read()
                except Exception as error:
                    await ctx.send(f"Couldn't download {emoji[1]}, {type(error).__name__}: {error}")
                    return
                try:
                    added = await ctx.guild.create_custom_emoji(name=emoji[1], image=image)
                except Exception as error:
                    await ctx.send(f"Couldn't upload {emoji[1]}, {type(error).__name__}: {error}")
                    return
                try:
                    await ctx.message.add_reaction(added)
                except:
                    pass

    @commands.command(name="+1", aliases=["rep", "giverep"])
    @commands.cooldown(rate=1, per=3600, type=commands.BucketType.user)
    async def rep(self, ctx: commands.Context, user: discord.User = None):
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
            with open(REP_FILE, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            with open(REP_FILE, 'w+'):
                data = {}
        count = data.get(str(user.id), 0) + 1
        data[str(user.id)] = count
        with open(REP_FILE, 'w') as file:
            json.dump(data, file)
        await ctx.send(f'{user.mention} +1 rep!')
        print(f'User {ctx.author.id} now has {count} rep')

    @rep.error
    async def rep_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send("You already gave a rep in the last hour!")

    @commands.command(aliases=["paintme", "paint", "drawme"])
    async def draw(self, ctx: commands.Context, user: Union[discord.User, str] = None):
        """Produces a painting of you or someone else"""
        if user == "me" or user is None:
            user = ctx.author
        elif user == "you" or user == "yourself":
            user = self.bot.user
        elif isinstance(user, str):
            return await ctx.send("who?")
        # load image
        await user.avatar_url.save(IMG_DL)
        Image.open(IMG_DL).convert('RGB').resize((256, 256), Image.BICUBIC).save(IMG_OUT)
        img = cv2.imread(IMG_OUT, cv2.IMREAD_COLOR)
        # apply morphology open to smooth the outline
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
        morph = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
        # brighten dark regions
        result = cv2.normalize(morph, None, 20, 255, cv2.NORM_MINMAX)
        # save and send
        cv2.imwrite(IMG_OUT, result)
        await ctx.send(file=discord.File(IMG_OUT))
        os.remove(IMG_DL)
        os.remove(IMG_OUT)
        print(f"Successfully painted user {user.id}")

    @commands.command(aliases=["showrep"])
    async def getrep(self, ctx: commands.Context, user: discord.User = None):
        """Gets the reputation points for a user"""
        if not user:
            user = ctx.author
        try:
            with open(REP_FILE, 'r') as file:
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
    async def pp(self, ctx: commands.Context):
        """Evaluates your pp"""
        pp = ctx.author.id % 13
        await ctx.send(f'Your pp size is {pp} inches')
        print(f'pp {ctx.author.id} {pp}')

def setup(bot: commands.Bot):
    bot.add_cog(Fun(bot))
