import discord
import random
from discord.ext import commands


class General(commands.Cog):
    """General commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["hello"])
    async def hi(self, ctx: commands.Context):
        """Greets"""
        await ctx.send('hi!')
        print('hi')

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """pong"""
        await ctx.send('pong')

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def say(self, ctx: commands.Context, *, msg):
        """Says something. Requires Manage Messages permission."""
        await ctx.message.delete()
        await ctx.send(msg)
        print('say {msg}')

    @commands.command()
    async def about(self, ctx: commands.Context):
        """Sends information about the bot and its owner"""
        await ctx.send('This bot was made for fun in homage to my friend Grey. My owner is <@871733390251012147>')

    @commands.command()
    async def pain(self, ctx: commands.Context):
        """Expresses pain"""
        emote = random.choice(['<:painpeko:846703815692648448>', '<:pain:756862045604806746>', '<:hidethepain:756862045194027008>'])
        await ctx.message.add_reaction(emote)

    @commands.command(aliases=["orange"])
    async def eat(self, ctx: commands.Context):
        """Eats"""
        emote = random.choice(['🍊', '🍩', '🍕', '🍗'])
        await ctx.message.add_reaction(emote)

    @commands.command(aliases=["sad"])
    async def cry(self, ctx: commands.Context):
        """Cries"""
        emote = random.choice(['😢', '😭', '😿', '<:peeposad:757725678878851112>', '<:vivicry:757245413626740847>', '<:dylancry:865017375756648448>'])
        await ctx.message.add_reaction(emote)


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
        embed = discord.Embed(title=f'{cog.qualified_name} Commands', colour=self.COLOR, description=cog.description)
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        for command in filtered:
            embed.add_field(name=self.get_command_signature(command), value=command.short_doc or '...', inline=False)

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
    bot.help_command = EmbedHelpCommand()
