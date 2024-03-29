import json
import discord
from random import random, choice
from discord.ext import commands

genshin_file = "genshin.json"

moment_of_bloom = {
    "5starfeatured": ["Hu Tao"],
    "5star": ["Keqing", "Mona", "Qiqi", "Diluc", "Jean"],
    "5starweapon": [],
    "4starfeatured": ["Chongyun", "Xingqiu", "Xiangling"],
    "4star": [
        "Xinyan", "Sucrose", "Diona", "Noelle", "Bennett", "Fischl", "Ningguang", "Beidou", "Razor", "Barbara"],
    "4starweapon": [
        "Rust", "Sacrificial Bow", "The Stringless", "Favonius Warbow", "Eye of Perception",
        "Sacrificial Fragments", "The Widsith", "Favonius Codex", "Favonius Lance", "Dragon's Bane",
        "Rainslasher", "Sacrificial Greatsword", "The Bell", "Favonius Greatsword", "Lions Roar",
        "Sacrificial Sword", "The Flute", "Favonius Sword"],
    "3star": [
        "Slingshot", "Sharpshooter's Oath", "Raven Bow", "Emerald Orb", "Thrilling Tales of Dragon Slayers",
        "Magic Guide", "Black Tassel", "Debate Club", "Bloodtainted Greatsword", "Ferrous Shadow",
        "Skyrider Sword", "Harbinger of Dawn", "Cool Steel"]
}
fivestars = moment_of_bloom["5star"] + moment_of_bloom["5starfeatured"] + moment_of_bloom["5starweapon"]
fourstars = moment_of_bloom["4star"] + moment_of_bloom["4starfeatured"] + moment_of_bloom["4starweapon"]
pull_img = {
    "Hu Tao": "https://cdn.discordapp.com/attachments/541768631445618689/818653017892061194/unknown.png"
}
wish_img = "https://cdn.discordapp.com/attachments/541768631445618689/818649843202916362/unknown.png"
wish_img4 = "https://media.discordapp.net/attachments/541768631445618689/879785351579832371/wish4.png"
wish_img5 = "https://cdn.discordapp.com/attachments/541768631445618689/879785356382330901/wish5.png"


class Genshin(commands.Cog):
    """Genshin Impact banner simulator commands"""
    def __init__(self, bot):
        self.bot = bot
        self.banner = moment_of_bloom

    def pull(self, userdata):
        roll = random()
        if userdata["no5starf"] >= 179:  # featured 5 star pity
            possible = self.banner["5starfeatured"]
        elif userdata["no5star"] >= 89 or roll < 0.006:  # 5 star
            if random() > 0.5:
                possible = self.banner["5starfeatured"]
            elif random() > 0.5 and self.banner["5starweapon"]:
                possible = self.banner["5starweapon"]
            else:
                possible = self.banner["5star"]
        elif userdata["no4starf"] >= 19:  # featured 4 star pity
            possible = self.banner["4starfeatured"]
        elif userdata["no4star"] >= 9 or roll < 0.051:  # 4 star
            if random() > 0.5:
                possible = self.banner["4starfeatured"]
            elif random() > 0.5 and self.banner["4starweapon"]:
                possible = self.banner["4starweapon"]
            else:
                possible = self.banner["4star"]
        else:  # 3 star
            possible = self.banner["3star"]

        result = choice(possible)
        if result in fourstars:
            userdata["no4star"] = 0
            if result in self.banner["4starfeatured"]:
                userdata["no4starf"] = 0
            else:
                userdata["no4starf"] += 1
            userdata["no5star"] += 1
            userdata["no5starf"] += 1
        else:
            userdata["no4star"] += 1
            userdata["no4starf"] += 1
            if result in fivestars:
                userdata["no5star"] = 0
                if result in self.banner["5starfeatured"]:
                    userdata["no5starf"] = 0
                else:
                    userdata["no5starf"] += 1
            else:
                userdata["no5star"] += 1

        userdata["inv"][result] = userdata["inv"].get(result, 0) + 1
        return result

    def pullx(self, uid, x):
        try:
            with open(genshin_file, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            with open(genshin_file, 'w+'):
                data = {}
        userdata = data.get(uid, {"no4star": 0, "no4starf": 0, "no5star": 0, "no5starf": 0, "inv": {}})
        pulled = []
        for _ in range(x):
            pulled.append(self.pull(userdata))
        data[uid] = userdata
        with open(genshin_file, 'w') as file:
            json.dump(data, file)
        return pulled

    @classmethod
    def formatitem(cls, item):
        return f'{item}{" ⭐⭐⭐⭐⭐" if item in fivestars else ""}{" ⭐⭐⭐⭐" if item in fourstars else ""}'

    @commands.command(aliases=["pull", "wish"])
    async def pull1(self, ctx: commands.Context, *, etc=""):
        """Makes 1 Genshin Impact wish (Hu Tao banner)"""
        if etc == '10':
            return await self.pull10(ctx)
        pulled = self.pullx(str(ctx.author.id), 1)[0]
        embed = discord.Embed(title="Your pull", description=self.formatitem(pulled), color=0xff0000)
        embed.set_thumbnail(url=wish_img5 if pulled in fivestars else wish_img4 if pulled in fourstars else wish_img)
        embed.set_image(url=pull_img.get(pulled, ""))
        await ctx.send(embed=embed)

    @commands.command(aliases=["wish10"])
    async def pull10(self, ctx: commands.Context):
        """Makes 10 Genshin Impact wishes (Hu Tao banner)"""
        pulled = self.pullx(str(ctx.author.id), 10)
        pulledf = "\n".join(self.formatitem(p) for p in pulled)
        embed = discord.Embed(title="Your pulls", description=f"```md\n{pulledf}```", color=0xff0000)
        embed.set_thumbnail(url=wish_img5 if any(p in fivestars for p in pulled) else
                            wish_img4 if any(p in fourstars for p in pulled) else wish_img)
        embed.set_image(url=next((pull_img.get(p) for p in pulled if p in pull_img), ""))

        await ctx.send(embed=embed)

    @commands.command(aliases=["inventory"])
    async def inv(self, ctx: commands.Context):
        """View your Genshin Impact inventory"""
        try:
            with open(genshin_file, 'r') as file:
                data = json.load(file)
        except FileNotFoundError:
            with open(genshin_file, 'w+'):
                data = {}
        userdata = data.get(str(ctx.author.id), None)
        if userdata is None or not userdata["inv"]:
            await ctx.send("You haven't pulled anything yet.")
        else:
            s = "```md"
            for key, value in userdata["inv"].items():
                if key not in self.banner["3star"]:
                    s += f'\n{value} x {key}{" ⭐⭐⭐⭐⭐" if key in fivestars else ""}'
            await ctx.send(embed=discord.Embed(title="Your inventory", description=s + "```", color=0x00ff00))

async def setup(bot: commands.Bot):
    await bot.add_cog(Genshin(bot))
