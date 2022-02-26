import disnake
from disnake.ext import commands

import os
import json
import sys

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found!")
else:
    with open("config.json") as file:
        config = json.load(file)

class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="ping",
                            description="get bot's latency",
                            guild_ids=config['guilds'])
    async def ping(self, inter: disnake.ApplicationCommandInteraction):
        """get the bot's current websocket latency."""
        await inter.response.send_message(
            f"pong! {round(self.bot.latency * 1000)}ms")


def setup(bot: commands.Bot):
    bot.add_cog(General(bot))
