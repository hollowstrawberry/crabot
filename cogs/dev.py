import io
import traceback
import textwrap
from discord.ext import commands
from contextlib import redirect_stdout

class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=["run"])
    @commands.is_owner()
    async def eval(self, ctx, *, body: str):
        """Evaluates a piece of code"""
        env = {
            'bot': self.bot,
            'ctx': ctx,
            'channel': ctx.channel,
            'author': ctx.author,
            'guild': ctx.guild,
            'message': ctx.message,
        }
        env.update(globals())
        stdout = io.StringIO()

        body = body.strip('` \n')
        if body.startswith('py\n'):
            body = body[3:]
        if '\n' not in body and ';' not in body and 'await' not in body:
            body = 'return ' + body
        body = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            print(body)
            exec(body, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n```')

        func = env['func']
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
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
    async def reload(self, ctx: commands.Context):
        """Reloads the bot"""
        for cog in tuple(self.bot.extensions.keys()):
            self.bot.reload_extension(cog)
        await ctx.message.add_reaction('\u2705')

def setup(bot: commands.Bot):
    bot.add_cog(Dev(bot))
