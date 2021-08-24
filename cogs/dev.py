import os
import io
import traceback
import textwrap
from contextlib import redirect_stdout
from discord.ext import commands
from discord.ext.commands import Context

class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=["run"])
    @commands.is_owner()
    async def eval(self, ctx: Context, *, body: str):
        """Evaluates a piece of code"""
        env = {'bot': self.bot, 'ctx': ctx}
        env.update(globals())
        stdout = io.StringIO()

        body = body.strip('` \n')
        if body.startswith('py\n'):
            body = body[3:].strip()
        if '\n' not in body and ';' not in body and 'await' not in body:
            body = 'return ' + body
        body = f'async def func():\n{textwrap.indent(body, "    ")}'

        try:
            print(body)
            exec(body, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except:
            value = stdout.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = stdout.getvalue()
            try:
                await ctx.message.add_reaction('\u2705')
            except:
                pass

            if ret is None:
                if value:
                    await ctx.send(f'```py\n{value}\n```')
            else:
                await ctx.send(f'```py\n{value}{ret}\n```')

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx: Context):
        """Reloads the bot's cogs"""
        for cog in tuple(self.bot.extensions.keys()):
            self.bot.reload_extension(cog)
        await ctx.message.add_reaction('✅')

    @commands.command()
    @commands.is_owner()
    async def update(self, ctx: Context):
        """Updates the bot then reloads the cogs"""
        # Update files from github
        stream = os.popen('git pull')
        output = stream.read()
        if 'Already up to date' in output:
            output = ""
        cogs = tuple(self.bot.extensions.keys())
        # Existing cogs
        for cog in cogs:
            try:
                self.bot.reload_extension(cog)
            except commands.ExtensionFailed as e:
                output += f'\n\n{e}'
        # New cogs
        for filename in os.listdir('./cogs'):
            newcog = f'cogs.{filename[:-3]}'
            if filename.endswith('.py') and newcog not in cogs:
                try:
                    self.bot.load_extension(newcog)
                except commands.NoEntryPointError:
                    pass
                except commands.ExtensionFailed as e:
                    output += f'\n\n{e}'
        if output:
            await ctx.send(f'```{output}```')
        else:
            await ctx.message.add_reaction('✅')

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error: commands.CommandError):
        if isinstance(error, commands.NotOwner):
            await ctx.message.add_reaction('❌')


def setup(bot: commands.Bot):
    bot.add_cog(Dev(bot))
