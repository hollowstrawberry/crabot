import discord
from discord.ext import commands
from discord.ext.commands import Context


class General(commands.Cog):
    """General commands"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def say(self, ctx: Context, *, msg):
        """Says something. Requires Manage Messages permission."""
        await ctx.message.delete()
        await ctx.send(msg)
        print('say {msg}')


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

    async def send_command_help(self, cmd: commands.Command):
        embed = discord.Embed(title=cmd.qualified_name, colour=self.COLOR, description="")
        if cmd.help:
            embed.description += cmd.help
        if cmd.aliases:
            embed.add_field(name="Aliases", value=','.join(f'`{c}`' for c in cmd.aliases))
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
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
