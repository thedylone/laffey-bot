import disnake
from disnake.ext import commands

import os
import random

from helpers import json_helper, general_helper

HOLODEX_TOKEN = os.environ["HOLODEX_TOKEN"]


class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="ping", description="get bot's latency")
    async def ping(self, inter: disnake.ApplicationCommandInteraction):
        """get the bot's current websocket latency."""
        await inter.response.send_message(f"pong! {round(self.bot.latency * 1000)}ms")

    @commands.slash_command(name="shouldiorder", description="should you get indulge?")
    async def rng(self, inter: disnake.ApplicationCommandInteraction):
        """should you get indulge?"""
        results = ["Hell yea boiii", "Nah save monet tday sadge"]
        await inter.response.send_message(
            f"<@{inter.author.id}> {random.choice(results)}"
        )

    @commands.slash_command(name="peko", description="peko")
    async def peko(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        """peko"""
        content, embed, view = await general_helper.peko(inter)
        await inter.edit_original_message(content=content, embed=embed, view=view)

    @commands.slash_command(name="holo", description="all live hololive streams")
    async def holo(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        """all live hololive streams"""
        content, embed, view = await general_helper.holo(inter)
        await inter.edit_original_message(content=content, embed=embed, view=view)


class GeneralAdmin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="prefix", description="set prefix for the server")
    @commands.has_guild_permissions(manage_messages=True)
    async def prefix(
        self, inter: disnake.ApplicationCommandInteraction, prefix: str = None
    ):
        await inter.response.defer()
        """set prefix for the server"""
        guild_data = json_helper.load("guildData.json")
        if prefix == None:
            current_prefix = guild_data[str(inter.guild.id)]["prefix"]
            await inter.edit_original_message(
                content=f'current prefix: {current_prefix}\nuse {current_prefix}prefix "<new prefix>" to change the prefix (include "" for multiple worded prefix)'
            )
        else:
            guild_data[str(inter.guild.id)]["prefix"] = prefix
            json_helper.save(guild_data, "guildData.json")
            await inter.edit_original_message(
                content=f"<@{inter.author.id}> successfully saved {prefix} as new server prefix"
            )


def setup(bot: commands.Bot):
    bot.add_cog(General(bot))
    bot.add_cog(GeneralAdmin(bot))
