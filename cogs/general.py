import discord
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

    @commands.command(aliases=["orange"])
    async def eat(self, ctx: commands.Context):
        """Eats"""
        await ctx.message.add_reaction('🍊')
        print('eat')

    @commands.command(aliases=["sad"])
    async def cry(self, ctx: commands.Context):
        """Cries"""
        await ctx.message.add_reaction('😭')
        print('cry')


class EmbedHelpCommand(commands.HelpCommand):
    COLOUR = discord.Colour(int('FCDF99', 16))

    def get_command_signature(self, command):
        return f'{command.qualified_name} {command.signature}'

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='Grey Commands', colour=self.COLOUR)
        description = self.context.bot.description
        if description:
            embed.description = description

        for cog, cmds in mapping.items():
            name = 'No Category' if cog is None else cog.qualified_name
            filtered = await self.filter_commands(cmds, sort=True)
            if filtered:
                value = '\n'.join(f'`{c.name}` - {c.short_doc}' for c in filtered)
                embed.add_field(name=name, value=value, inline=False)

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(title=f'{cog.qualified_name} Commands', colour=self.COLOUR)
        if cog.description:
            embed.description = cog.description

        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        for command in filtered:
            embed.add_field(name=self.get_command_signature(command), value=command.short_doc or '...', inline=False)

        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title=group.qualified_name, colour=self.COLOUR)
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
