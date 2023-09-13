"""prefix commands for crypto related commands"""
from disnake import Message
from disnake.ext import commands

from helpers import crypto


class Crypto(commands.Cog, name="crypto"):
    """crypto related commands"""

    COG_EMOJI: str = "💰"

    @commands.command(
        name="sol", description="get the current price of SOL in USD"
    )
    async def sol(self, ctx: commands.Context) -> None:
        """get the current price of SOL in USD"""
        message: Message = await ctx.reply("fetching price...")
        async with ctx.typing():
            await message.edit(**await crypto.price("SOL"))

    @commands.command(
        name="btc", description="get the current price of BTC in USD"
    )
    async def btc(self, ctx: commands.Context) -> None:
        """get the current price of BTC in USD"""
        message: Message = await ctx.reply("fetching price...")
        async with ctx.typing():
            await message.edit(**await crypto.price("BTC"))

    @commands.command(
        name="eth", description="get the current price of ETH in USD"
    )
    async def eth(self, ctx: commands.Context) -> None:
        """get the current price of ETH in USD"""
        message: Message = await ctx.reply("fetching price...")
        async with ctx.typing():
            await message.edit(**await crypto.price("ETH"))


def setup(bot: commands.Bot) -> None:
    """loads crypto cog into bot"""
    bot.add_cog(Crypto())
