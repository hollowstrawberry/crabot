import os
import io
import traceback
import textwrap
import discord
import time
import datetime
import psutil
import matplotlib.pyplot as plt
import PIL.ImageOps
from contextlib import redirect_stdout
from discord.ext import commands
from discord.ext.commands import Context
from gpiozero import *
from PIL import Image, ImageDraw, ImageFont

cpu_load = []  # 0/100
disk_load = []  # same
ram_load = []  # 0/1

TimeRef = []
for h in range(60):
    TimeRef.append(int(h))

Start = round(time.time())

GRAPH_IMG = "temp.png"

class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.loop.create_task(self.get_stats())

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

    def get_ram(self):
        p = os.popen('free')
        i = 0
        while 1:
            i = i + 1
            line = p.readline()
            if i == 2:
                return line.split()[1:4]

    running = True

    def cog_unload(self):
        super().cog_unload()
        self.running = False

    async def get_stats(self):
        while self.running:
            load = round(psutil.cpu_percent())
            disk = DiskUsage()
            ram = round(int(self.get_ram()[1]) / 1000)

            if len(cpu_load) < 60:
                cpu_load.append(load)
            else:
                cpu_load.pop(0)
                cpu_load.append(load)

            if len(disk_load) < 60:
                disk_load.append(round(disk.usage))
            else:
                disk_load.pop(0)
                disk_load.append(round(disk.usage))

            if len(ram_load) < 60:
                ram_load.append(ram)
            else:
                ram_load.pop(0)
                ram_load.append(ram)

    @commands.command()
    @commands.is_owner()
    async def cpu(self, ctx):
        lap = round(time.time())

        plt.plot(TimeRef, cpu_load, color='#A79A0D', linewidth=3)  # *Load : discord Blue
        plt.xlabel("Time in minutes")
        plt.ylabel("% of use")
        plt.legend(labels="a", loc=(2.0, 0.15))
        plt.savefig(GRAPH_IMG, dpi=80, bbox_inches='tight', transparent=True)

        font = ImageFont.truetype("arial.ttf", size=30)
        transparent_area = (851, 224, 943, 262)
        text = f"""Additional Info :\nCPU : 1.2GHz ARM Cortex-A53
        \n\nUptime:\n{datetime.timedelta(seconds=(lap - Start))}\n\n\n    : CPU Load - {cpu_load[-1]}%"""

        image = Image.open(GRAPH_IMG)
        if image.mode == 'RGBA':
            r, g, b, a = image.split()
            rgb_image = Image.merge('RGB', (r, g, b))

            inverted_image = PIL.ImageOps.invert(rgb_image)

            r2, g2, b2 = inverted_image.split()

            final_transparent_image = Image.merge('RGBA', (r2, g2, b2, a))

            final_transparent_image.save(GRAPH_IMG)

        else:
            inverted_image = PIL.ImageOps.invert(image)
            inverted_image.save(GRAPH_IMG)

        image2 = Image.open(GRAPH_IMG)
        edit_image = ImageDraw.Draw(image2)
        edit_image.rectangle(transparent_area, fill=0)
        edit_image.text((499, 10), text, font=font)
        edit_image.rounded_rectangle((500, 243, 522, 265), fill="#5865F2", outline="#5865F2", width=3, radius=7)
        image2.save(GRAPH_IMG)

        file = discord.File(GRAPH_IMG, filename=GRAPH_IMG)
        graph_embed = discord.Embed(title="Server info : CPU Load in %")
        graph_embed.set_image(url=f"attachment://{GRAPH_IMG}")
        await ctx.message.reply(file=file, embed=graph_embed, mention_author=False)
        plt.cla()
        plt.clf()
        os.remove(GRAPH_IMG)

    @commands.command(aliases=['diskusage'])
    @commands.is_owner()
    async def disk(self, ctx):
        lap = round(time.time())

        plt.plot(TimeRef, disk_load, color='#0da79a', linewidth=3)  # * Disk : red-ish
        plt.xlabel("Time in minutes")
        plt.ylabel("% of use")
        plt.legend(labels="a", loc=(2.0, 0.15))
        plt.savefig(GRAPH_IMG, dpi=80, bbox_inches='tight', transparent=True)

        font = ImageFont.truetype("arial.ttf", size=30)
        transparent_area = (851, 224, 943, 262)
        text = f"""Additional Info :\n32Gb samsung Micro SD card\n\nUptime:\n{datetime.timedelta(seconds=(lap - Start))}
        \n\n\n    : Disk Use - {disk_load[-1]}%"""

        image = Image.open(GRAPH_IMG)
        if image.mode == 'RGBA':
            r, g, b, a = image.split()
            rgb_image = Image.merge('RGB', (r, g, b))

            inverted_image = PIL.ImageOps.invert(rgb_image)

            r2, g2, b2 = inverted_image.split()

            final_transparent_image = Image.merge('RGBA', (r2, g2, b2, a))

            final_transparent_image.save(GRAPH_IMG)

        else:
            inverted_image = PIL.ImageOps.invert(image)
            inverted_image.save(GRAPH_IMG)

        image2 = Image.open(GRAPH_IMG)
        edit_image = ImageDraw.Draw(image2)
        edit_image.rectangle(transparent_area, fill=0)
        edit_image.text((499, 10), text, font=font)
        edit_image.rounded_rectangle((500, 243, 522, 265), fill="#f25865", outline="#f25865", width=3, radius=7)
        image2.save(GRAPH_IMG)

        file = discord.File(GRAPH_IMG, filename=GRAPH_IMG)
        graph_embed = discord.Embed(title="Server info : Disk Use in %")
        graph_embed.set_image(url=f"attachment://{GRAPH_IMG}")
        await ctx.message.reply(file=file, embed=graph_embed, mention_author=False)
        plt.cla()
        plt.clf()
        os.remove(GRAPH_IMG)

    @commands.command()
    @commands.is_owner()
    async def ram(self, ctx):
        lap = round(time.time())
        plt.plot(TimeRef, ram_load, color='#0559e5', linewidth=3)  # * RAM : Yellow-ish
        plt.xlabel("Time in minutes")
        plt.ylabel("RAM USage in Mb")
        plt.legend(labels="a", loc=(2.0, 0.15))
        plt.savefig(GRAPH_IMG, dpi=80, bbox_inches='tight', transparent=True)

        font = ImageFont.truetype("arial.ttf", size=30)
        transparent_area = (851, 224, 943, 262)
        text = f"""Additional Info :\n1Gb 500 MHz RAM\n\nUptime:\n{datetime.timedelta(seconds=(lap - Start))}
        \n\n\n    : RAM Usage - {ram_load[-1]}Mb"""

        image = Image.open(GRAPH_IMG)
        if image.mode == 'RGBA':
            r, g, b, a = image.split()
            rgb_image = Image.merge('RGB', (r, g, b))

            inverted_image = PIL.ImageOps.invert(rgb_image)

            r2, g2, b2 = inverted_image.split()

            final_transparent_image = Image.merge('RGBA', (r2, g2, b2, a))

            final_transparent_image.save(GRAPH_IMG)

        else:
            inverted_image = PIL.ImageOps.invert(image)
            inverted_image.save(GRAPH_IMG)

        image2 = Image.open(GRAPH_IMG)
        edit_image = ImageDraw.Draw(image2)
        edit_image.rectangle(transparent_area, fill=0)
        edit_image.text((499, 10), text, font=font)
        edit_image.rounded_rectangle((500, 243, 522, 265), fill="#faa61a", outline="#faa61a", width=3, radius=7)
        image2.save(GRAPH_IMG)

        file = discord.File(GRAPH_IMG, filename=GRAPH_IMG)
        graph_embed = discord.Embed(title="Server info : RAM usage in Mb for a total of 1Gb")
        graph_embed.set_image(url=f"attachment://{GRAPH_IMG}")
        await ctx.message.reply(file=file, embed=graph_embed, mention_author=False)
        plt.cla()
        plt.clf()
        os.remove(GRAPH_IMG)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error: commands.CommandError):
        if isinstance(error, commands.NotOwner):
            await ctx.message.add_reaction('❌')


def setup(bot: commands.Bot):
    bot.add_cog(Dev(bot))
