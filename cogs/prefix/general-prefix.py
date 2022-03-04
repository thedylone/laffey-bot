import disnake
import random
from disnake.ext import commands

import os
import json
import sys
import aiohttp
import re

from views.views import Menu

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found!")
else:
    with open("config.json", encoding="utf-8") as file:
        config = json.load(file)

HOLODEX_TOKEN = os.environ["HOLODEX_TOKEN"]


class General(commands.Cog, name="general"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping", description="get bot's latency")
    async def ping(self, ctx: commands.Context):
        """get the bot's current websocket latency."""
        await ctx.send(f"pong! {round(self.bot.latency * 1000)}ms")

    @commands.command(name="flip", description="flip a coin and show the result")
    async def ping(self, ctx: commands.Context):
        """flips a coin kekg"""
        results = ["Heads!", "Tails!"]
        await ctx.send(f"<@{ctx.author.id}> You got... {random.choice(results)}")

    @commands.command(name="peko", description="peko")
    async def peko(self, ctx: commands.Context):
        """peko"""
        url = "https://holodex.net/api/v2/users/live"
        params = {
            "channels": "UC1DCedRgGHBdm81E1llLhOQ,UCdn5BQ06XqgXoAxIhbqw5Rg,UC5CwaMl1eIgY8h02uZw7u8A,UChAnqc_AY5_I3Px5dig3X1Q"
        }
        headers = {"Content-Type": "application/json", "X-APIKEY": HOLODEX_TOKEN}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as request:
                if request.status == 200:
                    data = await request.json()
                    if data:
                        embeds = []
                        step = 5  # number of vids per embed
                        for i in range(0, len(data), step):
                            embed = disnake.Embed(
                                title="hololive",
                                description="[live and upcoming videos](https://holodex.net/)",
                            )
                            embed.set_thumbnail(
                                url="https://hololive.hololivepro.com/wp-content/themes/hololive/images/head_l.png"
                            )
                            for video in data[i : i + step]:
                                pattern = "\[|\]"
                                embed.add_field(
                                    name=video["channel"]["name"],
                                    value=f"[{re.sub(pattern,'',video['title'])}](https://www.youtube.com/watch?v={video['id']})",
                                    inline=False,
                                )
                            embeds.append(embed)
                        if len(data) > step:
                            await ctx.send(embed=embeds[0], view=Menu(embeds))
                        else:
                            await ctx.send(embed=embeds[0])
                    else:
                        embed = disnake.Embed(
                            title="hololive",
                            description="[live and upcoming videos](https://holodex.net/)",
                        )
                        embed.set_thumbnail(
                            url="https://hololive.hololivepro.com/wp-content/themes/hololive/images/head_l.png"
                        )
                        embed.add_field(
                            name="sadger badger", value="no strim rn", inline=False
                        )
                        await ctx.send(embed=embed)
                else:
                    await ctx.send(
                        f"<@{ctx.author.id}> error retrieving info! try again later"
                    )

    @commands.command(name="holo", description="all live hololive streams")
    async def holo(self, ctx: commands.Context):
        """all live hololive streams"""
        url = "https://holodex.net/api/v2/live"
        params = {"status": "live", "org": "Hololive", "limit": "50"}
        headers = {"Content-Type": "application/json", "X-APIKEY": HOLODEX_TOKEN}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as request:
                if request.status == 200:
                    data = await request.json()
                    if data:
                        embeds = []
                        step = 5  # number of vids per embed
                        for i in range(0, len(data), step):
                            embed = disnake.Embed(
                                title="hololive",
                                description="[live and upcoming videos](https://holodex.net/)",
                            )
                            embed.set_thumbnail(
                                url="https://hololive.hololivepro.com/wp-content/themes/hololive/images/head_l.png"
                            )
                            for video in data[i : i + step]:
                                pattern = "\[|\]"
                                embed.add_field(
                                    name=video["channel"]["name"],
                                    value=f"[{re.sub(pattern,'',video['title'])}](https://www.youtube.com/watch?v={video['id']})",
                                    inline=False,
                                )
                            embeds.append(embed)
                        if len(data) > step:
                            await ctx.send(embed=embeds[0], view=Menu(embeds))
                        else:
                            await ctx.send(embed=embeds[0])
                    else:
                        embed = disnake.Embed(
                            title="hololive",
                            description="[live and upcoming videos](https://holodex.net/)",
                        )
                        embed.set_thumbnail(
                            url="https://hololive.hololivepro.com/wp-content/themes/hololive/images/head_l.png"
                        )
                        embed.add_field(
                            name="sadger badger", value="no strim rn", inline=False
                        )
                        await ctx.send(embed=embed)
                else:
                    await ctx.send(
                        f"<@{ctx.author.id}> error retrieving info! try again later"
                    )


def setup(bot: commands.Bot):
    bot.add_cog(General(bot))
