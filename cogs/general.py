import re
import json
import discord
import inspect
import textwrap
from discord.ext import commands
from typing import *

class General(commands.Cog):
    """General commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.prefix: Optional[re.Pattern] = None
        bot.command_prefix = self.get_prefix

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(activity=discord.Game('Minecraft'), status=discord.Status.online)
        print('Ready')

    def get_prefix(self, bot: commands.Bot, message: discord.Message):
        if not self.prefix:
            self.prefix = re.compile(fr'^(crab(ot)?|<@!?{bot.user.id}>),? ?', re.IGNORECASE)
        if message.guild and message.guild.id == 930471371128061962 and message.content.startswith('!'):
            return '!'
        return match.group() if (match := self.prefix.match(message.content)) else 'crab '

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx: commands.Context, *, msg):
        """Repeats something you say. Only works for moderators"""
        try:
            await ctx.message.delete()
        except:
            pass
        await ctx.send(msg)
        print('say {msg}')

    @commands.command(aliases=["python"])
    async def code(self, ctx: commands.Context, name):
        """Sends the code that makes up a command or function of this bot"""
        predicate = lambda x: inspect.ismethod(x) or isinstance(x, commands.Command)
        functions = [inspect.getmembers(cog, predicate=predicate) for cog in self.bot.cogs.values()]
        functions = dict(fn for cog in functions for fn in cog))
        functions = {k: v.callback if isinstance(v, commands.Command) else v
                     for k, v in functions.items() if not k.startswith(('_', 'cog'))}
        try:
            code = inspect.getsource(functions[name])
            code = textwrap.dedent(code).replace("```", "`")[:1990]
            await ctx.send(f'```py\n{code}```')
        except KeyError:
            await ctx.send("Can't find a function with that name")


class EmbedHelpCommand(commands.HelpCommand):
    COLOR = discord.Color(int('FCDF99', 16))

    def get_command_signature(self, command: commands.Command):
        return f'{command.qualified_name} {command.signature}'

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title='Crab Commands', colour=self.COLOR,
                              description="Use help again on a command or category for more information!")
        for cog, cmds in mapping.items():
            name = 'No Category' if cog is None else cog.qualified_name
            filtered = await self.filter_commands(cmds, sort=True)
            if filtered:
                value = ', '.join(f'`{c.name}`' for c in filtered)
                embed.add_field(name=name, value=value, inline=True)

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        embed = discord.Embed(title=f'{cog.qualified_name} Commands', colour=self.COLOR,
                              description=cog.description)
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        for command in filtered:
            embed.add_field(name=self.get_command_signature(command),
                            value=command.short_doc or '...', inline=False)
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        embed = discord.Embed(title=command.qualified_name, colour=self.COLOR, description="")
        if command.help:
            embed.description += command.help
        if command.aliases:
            embed.add_field(name="Aliases", value=','.join(f'`{c}`' for c in command.aliases))
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        embed = discord.Embed(title=group.qualified_name, colour=self.COLOR, description="")
        if group.help:
            embed.description += group.help
        filtered = await self.filter_commands(group.commands, sort=True)
        for command in filtered:
            embed.add_field(name=self.get_command_signature(command), value=command.short_doc or '...',
                            inline=False)
        await self.get_destination().send(embed=embed)


def setup(bot: commands.Bot):
    cog = General(bot)
    bot.add_cog(cog)
    bot.help_command = EmbedHelpCommand()
    bot.help_command.cog = cog
