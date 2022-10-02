from disnake.ext import commands

from helpers import crypto_helper


class Crypto(commands.Cog, name="crypto"):
    """crypto related commands"""

    COG_EMOJI = "🪙"

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="sol", description="sol price")
    async def sol(self, ctx: commands.Context):
        """get the current price of SOL in USD."""
        content = await crypto_helper.price("SOLUSDT")
        await ctx.send(content=content)

    @commands.command(name="btc", description="btc price")
    async def btc(self, ctx: commands.Context):
        """get the current price of BTC in USD."""
        content = await crypto_helper.price("BTCUSDT")
        await ctx.send(content=content)

    @commands.command(name="eth", description="eth price")
    async def eth(self, ctx: commands.Context):
        """get the current price of ETH in USD."""
        content = await crypto_helper.price("ETHUSDT")
        await ctx.send(content=content)


def setup(bot: commands.Bot):
    bot.add_cog(Crypto(bot))
