from disnake import ApplicationCommandInteraction
from disnake.ext import commands

from helpers import crypto_helper


class Crypto(commands.Cog):
    """crypto related commands"""

    COG_EMOJI = "🪙"

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="sol", description="sol price")
    async def sol(self, inter: ApplicationCommandInteraction):
        """get the current price of SOL in USD."""
        await inter.response.defer()
        content = await crypto_helper.price("SOLUSDT")
        await inter.edit_original_message(content=content)

    @commands.slash_command(name="btc", description="btc price")
    async def btc(self, inter: ApplicationCommandInteraction):
        """get the current price of BTC in USD."""
        await inter.response.defer()
        content = await crypto_helper.price("BTCUSDT")
        await inter.edit_original_message(content=content)

    @commands.slash_command(name="eth", description="eth price")
    async def eth(self, inter: ApplicationCommandInteraction):
        """get the current price of ETH in USD."""
        await inter.response.defer()
        content = await crypto_helper.price("ETHUSDT")
        await inter.edit_original_message(content=content)


def setup(bot: commands.Bot):
    bot.add_cog(Crypto(bot))
