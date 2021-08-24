import re
import json
import hashlib
import aiohttp
from discord.ext import commands


class Fun(commands.Cog):
    """Commands you might actually want to use"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['quick,', 'math', 'wolfram'])
    async def quick(self, ctx: commands.Context, *, query: commands.clean_content):
        """Does a quick WolframAlpha query"""
        await ctx.channel.trigger_typing()
        async with aiohttp.ClientSession() as s:
            async with s.get(
                    'https://api.wolframalpha.com/v2/result',
                    params={'i': query, 'appid': self.bot.config['wolfram']}
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
    async def donut(self, ctx: commands.Context):
        """Gives you a donut"""
        try:
            with open('donuts.json', 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            with open('donuts.json', 'w+'):
                data = {}
        count = data.get(str(ctx.author.id), 0) + 1
        data[str(ctx.author.id)] = count
        with open('donuts.json', 'w') as file:
            json.dump(data, file)
        await ctx.send(f'{count} 🍩')
        print(f'User {ctx.author.id} now has {count} donuts')

    @commands.command()
    async def pp(self, ctx: commands.Context):
        """Evaluates your pp"""
        pp = ctx.author.id % 13
        await ctx.send(f'Your pp size is {pp} inches')
        print(f'pp {ctx.author.id} {pp}')

def setup(bot: commands.Bot):
    bot.add_cog(Fun(bot))
