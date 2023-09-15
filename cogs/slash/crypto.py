"""slash commands for crypto related commands"""
from disnake import ApplicationCommandInteraction
from disnake.ext.commands import Bot, Cog, slash_command

from helpers import crypto


class Crypto(Cog):
    """crypto related commands"""

    COG_EMOJI: str = "💰"

    @slash_command(
        name="sol", description="get the current price of SOL in USD"
    )
    async def sol(self, inter: ApplicationCommandInteraction) -> None:
        """get the current price of SOL in USD"""
        await inter.response.defer()
        await inter.edit_original_message(**await crypto.price("SOL"))

    @slash_command(
        name="btc", description="get the current price of BTC in USD"
    )
    async def btc(self, inter: ApplicationCommandInteraction) -> None:
        """get the current price of BTC in USD"""
        await inter.response.defer()
        await inter.edit_original_message(**await crypto.price("BTC"))

    @slash_command(
        name="eth", description="get the current price of ETH in USD"
    )
    async def eth(self, inter: ApplicationCommandInteraction) -> None:
        """get the current price of ETH in USD"""
        await inter.response.defer()
        await inter.edit_original_message(**await crypto.price("ETH"))


def setup(bot: Bot) -> None:
    """loads crypto cog into bot"""
    bot.add_cog(Crypto())
