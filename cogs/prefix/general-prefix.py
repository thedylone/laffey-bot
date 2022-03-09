import disnake
from disnake.ext import commands

import os
import random

from helpers import json_helper, general_helper

HOLODEX_TOKEN = os.environ["HOLODEX_TOKEN"]


class General(commands.Cog, name="general"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping", description="get bot's latency")
    async def ping(self, ctx: commands.Context):
        """get the bot's current websocket latency."""
        await ctx.send(f"pong! {round(self.bot.latency * 1000)}ms")

    @commands.command(name="shouldiorder", description="should you get indulge?")
    async def rng(self, ctx: commands.Context):
        """should you get indulge?"""
        results = ["Hell yea boiii", "Nah save monet tday sadge"]
        await ctx.send(f"<@{ctx.author.id}> {random.choice(results)}")

    @commands.command(name="peko", description="peko")
    async def peko(self, ctx: commands.Context):
        """peko"""
        content, embed, view = await general_helper.peko(ctx)
        await ctx.send(content=content, embed=embed, view=view)

    @commands.command(name="holo", description="all live hololive streams")
    async def holo(self, ctx: commands.Context):
        """all live hololive streams"""
        content, embed, view = await general_helper.holo(ctx)
        await ctx.send(content=content, embed=embed, view=view)


class GeneralAdmin(commands.Cog, name="general admin"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="prefix", description="set prefix for the server")
    @commands.has_guild_permissions(manage_messages=True)
    async def prefix(self, ctx: commands.Context, prefix: str = None):
        """set prefix for the server"""
        if prefix == None:
            await ctx.send(
                content=f'use {ctx.prefix}prefix "<new prefix>" (include "" for multiple worded prefix)'
            )
            return
        guild_data = json_helper.load("guildData.json")
        guild_data[str(ctx.guild.id)]["prefix"] = prefix
        json_helper.save(guild_data, "guildData.json")
        await ctx.send(
            f"<@{ctx.author.id}> successfully saved {prefix} as new server prefix"
        )


def setup(bot: commands.Bot):
    bot.add_cog(General(bot))
    bot.add_cog(GeneralAdmin(bot))
