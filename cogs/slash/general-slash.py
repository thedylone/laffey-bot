from disnake import ApplicationCommandInteraction
from disnake.ext import commands

import random

from helpers import general_helper


class General(commands.Cog):
    """miscellaneous bot commands"""

    COG_EMOJI = "🤖"

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="ping",
        description="get bot's latency",
    )
    async def ping(self, inter: ApplicationCommandInteraction):
        """get the bot's current websocket latency."""
        await inter.response.send_message(
            f"pong! {round(self.bot.latency * 1000)}ms"
        )

    @commands.slash_command(
        name="shouldiorder",
        description="should you get indulge?",
    )
    async def rng(self, inter: ApplicationCommandInteraction):
        """should you get indulge?"""
        results = ["Hell yea boiii", "Nah save monet tday sadge"]
        await inter.response.send_message(
            f"<@{inter.author.id}> {random.choice(results)}"
        )

    @commands.slash_command(
        name="peko",
        description="peko",
    )
    async def peko(self, inter: ApplicationCommandInteraction):
        """peko"""
        await inter.response.defer()
        content, embed, view = await general_helper.peko(inter)
        await inter.edit_original_message(
            content=content, embed=embed, view=view
        )

    @commands.slash_command(
        name="fubu",
        description="fubu",
    )
    async def fubu(self, inter: ApplicationCommandInteraction):
        """fubu"""
        await inter.response.defer()
        content, embed, view = await general_helper.fubu(inter)
        await inter.edit_original_message(
            content=content, embed=embed, view=view
        )

    @commands.slash_command(
        name="holo",
        description="all live hololive streams",
    )
    async def holo(self, inter: ApplicationCommandInteraction):
        """all live hololive streams"""
        await inter.response.defer()
        content, embed, view = await general_helper.holo(inter)
        await inter.edit_original_message(
            content=content, embed=embed, view=view
        )


class GeneralAdmin(commands.Cog):
    """bot admin commands"""

    COG_EMOJI = "📃"

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="prefix",
        description="set prefix for the server",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def prefix(
        self,
        inter: ApplicationCommandInteraction,
        prefix: str = None,
    ):
        """set prefix for the server"""
        await inter.response.defer()
        content = await general_helper.prefix(self.bot, inter, prefix)
        await inter.edit_original_message(content=content)


def setup(bot: commands.Bot):
    bot.add_cog(General(bot))
    bot.add_cog(GeneralAdmin(bot))
