import disnake
from disnake.ext import commands

import random

from helpers import general_helper


class General(commands.Cog, name="general"):
    """miscellaneous bot commands"""
    COG_EMOJI = "🤖"

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
    """bot admin commands"""
    COG_EMOJI = "📃"

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="prefix", description="set prefix for the server")
    @commands.has_guild_permissions(manage_messages=True)
    async def prefix(self, ctx: commands.Context, prefix: str = None):
        """set prefix for the server"""
        content = await general_helper.prefix(self.bot, ctx, prefix)
        await ctx.send(content=content)


def setup(bot: commands.Bot):
    bot.add_cog(General(bot))
    bot.add_cog(GeneralAdmin(bot))
