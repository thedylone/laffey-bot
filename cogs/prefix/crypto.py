"""prefix commands for crypto related commands"""

from disnake.ext import commands

from helpers import crypto_helper


class Crypto(commands.Cog, name="crypto"):
    """crypto related commands"""

    COG_EMOJI: str = "💰"

    @commands.command(name="sol", description="sol price")
    async def sol(self, ctx: commands.Context) -> None:
        """get the current price of SOL in USD."""
        await ctx.send(**await crypto_helper.price("SOL"))

    @commands.command(name="btc", description="btc price")
    async def btc(self, ctx: commands.Context) -> None:
        """get the current price of BTC in USD."""
        await ctx.send(**await crypto_helper.price("BTC"))

    @commands.command(name="eth", description="eth price")
    async def eth(self, ctx: commands.Context) -> None:
        """get the current price of ETH in USD."""
        await ctx.send(**await crypto_helper.price("ETH"))


def setup(bot: commands.Bot) -> None:
    """loads crypto cog into bot"""
    bot.add_cog(Crypto())
