"""slash commands for crypto related commands"""

from disnake import ApplicationCommandInteraction
from disnake.ext import commands

from helpers import crypto_helper


class Crypto(commands.Cog):
    """crypto related commands"""

    COG_EMOJI: str = "💰"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.slash_command(name="sol", description="sol price")
    async def sol(self, inter: ApplicationCommandInteraction) -> None:
        """get the current price of SOL in USD."""
        await inter.response.defer()
        await inter.edit_original_message(**await crypto_helper.price("SOL"))

    @commands.slash_command(name="btc", description="btc price")
    async def btc(self, inter: ApplicationCommandInteraction) -> None:
        """get the current price of BTC in USD."""
        await inter.edit_original_message(**await crypto_helper.price("BTC"))

    @commands.slash_command(name="eth", description="eth price")
    async def eth(self, inter: ApplicationCommandInteraction) -> None:
        """get the current price of ETH in USD."""
        await inter.response.defer()
        await inter.edit_original_message(**await crypto_helper.price("ETH"))


def setup(bot: commands.Bot) -> None:
    """loads crypto cog into bot"""
    bot.add_cog(Crypto(bot))
