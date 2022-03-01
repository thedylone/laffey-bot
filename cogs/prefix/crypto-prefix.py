import disnake
from disnake.ext import commands

import aiohttp


class Crypto(commands.Cog, name="crypto"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="sol", description="solprice")
    async def sol(self, ctx: commands.Context):
        """get the current price of SOL in USD."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT"
            ) as request:
                if request.status == 200:
                    data = await request.json()
                    await ctx.send("1 SOL is {:.2f} USD".format(float(data["price"])))
                else:
                    await ctx.send("error getting price")

    @commands.command(name="btc", description="btcprice")
    async def btc(self, ctx: commands.Context):
        """get the current price of BTC in USD."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
            ) as request:
                if request.status == 200:
                    data = await request.json()
                    await ctx.send("1 BTC is {:.2f} USD".format(float(data["price"])))
                else:
                    await ctx.send("error getting price")

    @commands.command(name="eth", description="ethprice")
    async def eth(self, ctx: commands.Context):
        """get the current price of ETH in USD."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT"
            ) as request:
                if request.status == 200:
                    data = await request.json()
                    await ctx.send("1 ETH is {:.2f} USD".format(float(data["price"])))
                else:
                    await ctx.send("error getting price")


def setup(bot: commands.Bot):
    bot.add_cog(Crypto(bot))
