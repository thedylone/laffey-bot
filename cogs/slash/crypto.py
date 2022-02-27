import disnake
from disnake.ext import commands

import os
import json
import sys
import aiohttp

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found!")
else:
    with open("config.json", encoding='utf-8') as file:
        config = json.load(file)


class Crypto(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name='sol',
                            description='solprice',
                            guild_ids=config['guilds'])
    async def sol(self, inter: disnake.ApplicationCommandInteraction):
        """get the current price of SOL in USD."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    'https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT'
            ) as request:
                if request.status == 200:
                    data = await request.json()
                    await inter.response.send_message(
                        "1 SOL is {:.2f} USD".format(float(data['price'])))
                else:
                    await inter.response.send_message("error getting price")


def setup(bot: commands.Bot):
    bot.add_cog(Crypto(bot))
