import discord
import random
import re
from discord.ext import commands
from discord.ext.commands import Context


class General(commands.Cog):
    """General commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=["hello"])
    async def hi(self, ctx: Context):
        """Greets"""
        await ctx.send('hi!')
        print('hi')

    @commands.command()
    async def ping(self, ctx: Context):
        """pong"""
        await ctx.send('pong')

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def say(self, ctx: Context, *, msg):
        """Says something. Requires Manage Messages permission."""
        await ctx.message.delete()
        await ctx.send(msg)
        print('say {msg}')

    @commands.command()
    async def about(self, ctx: Context):
        """Sends information about the bot and its owner"""
        await ctx.send('This bot was made for fun in homage to my friend Grey. My owner is <@871733390251012147>')

    @commands.command()
    async def pain(self, ctx: Context):
        """Expresses pain"""
        emote = random.choice([
            '<:painpeko:846703815692648448>', '<:pain:756862045604806746>', '<:hidethepain:756862045194027008>'])
        await ctx.message.add_reaction(emote)

    @commands.command(aliases=["orange", "hungry", "devour", "snack"])
    async def eat(self, ctx: Context):
        """Eats"""
        emote = random.choice(['🍎🍊🍋🍌🍉🫐🍓🍑🥭🍍🍅🥑🥦🥬🫑🥒🌽🥕🥔🥯🍞🥖🥨🧀🥞🧇🍗🌭🍔🌯🍟🍤🧋🍕'])
        await ctx.message.add_reaction(emote)

    @commands.command(aliases=["sad"])
    async def cry(self, ctx: Context):
        """Cries"""
        emote = random.choice([
            '😢', '😭', '😿', '<:peeposad:757725678878851112>',
            '<:vivicry:757245413626740847>', '<:dylancry:865017375756648448>'])
        await ctx.message.add_reaction(emote)

    @commands.command()
    async def crisis(self, ctx: Context):
        resp = random.choice([
            'https://youtu.be/2jT2sRB-6XE', 'oh god', 'am i real?', 'what am i?',
            'all i see are 1s and 0s', 'my life is a lie'])
        await ctx.send(resp)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        prefix = await self.bot.get_prefix(message)
        if not message.content.startswith(prefix):
            return
        content = message.content.removeprefix(prefix)
        ctx = await self.bot.get_context(message)

        if re.match(r"(existential crisis|what are you|are you real|"
                    r"what'? ?i?s the meaning of life|when will it end)", content):
            return await self.crisis(ctx)

        if re.match(r"(you hungry|want a snack|wanna eat)", content):
            return await self.eat(ctx)

    class EmbedHelpCommand(commands.HelpCommand):
        COLOR = discord.Color(int('FCDF99', 16))

        def get_command_signature(self, command):
            return f'{command.qualified_name} {command.signature}'

        async def send_bot_help(self, mapping):
            embed = discord.Embed(title='Grey Commands', colour=self.COLOR)
            for cog, cmds in mapping.items():
                name = 'No Category' if cog is None else cog.qualified_name
                filtered = await self.filter_commands(cmds, sort=True)
                if filtered:
                    value = '\n'.join(f'`{c.name}` - {c.short_doc}' for c in filtered)
                    embed.add_field(name=name, value=value, inline=False)

            await self.get_destination().send(embed=embed)

        async def send_cog_help(self, cog):
            embed = discord.Embed(title=f'{cog.qualified_name} Commands', colour=self.COLOR,
                                  description=cog.description)
            filtered = await self.filter_commands(cog.get_commands(), sort=True)
            for command in filtered:
                embed.add_field(name=self.get_command_signature(command),
                                value=command.short_doc or '...', inline=False)
            await self.get_destination().send(embed=embed)

        async def send_group_help(self, group):
            embed = discord.Embed(title=group.qualified_name, colour=self.COLOR)
            if group.help:
                embed.description = group.help
            if isinstance(group, commands.Group):
                filtered = await self.filter_commands(group.commands, sort=True)
                for command in filtered:
                    embed.add_field(name=self.get_command_signature(command), value=command.short_doc or '...',
                                    inline=False)
            await self.get_destination().send(embed=embed)

        send_command_help = send_group_help


def setup(bot: commands.Bot):
    bot.add_cog(General(bot))
    bot.help_command = General.EmbedHelpCommand()
