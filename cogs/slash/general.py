"""slash commands for general commands"""

import random
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

from helpers import general_helper


class General(commands.Cog):
    """miscellaneous bot commands"""

    COG_EMOJI = "🤖"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.slash_command(
        name="ping",
        description="get bot's latency",
    )
    async def ping(self, inter: ApplicationCommandInteraction) -> None:
        """get the bot's current websocket latency."""
        await inter.response.send_message(
            f"pong! {round(self.bot.latency * 1000)}ms"
        )

    @commands.slash_command(
        name="shouldiorder",
        description="should you get indulge?",
    )
    async def rng(self, inter: ApplicationCommandInteraction) -> None:
        """should you get indulge?"""
        results: list[str] = ["Hell yea boiii", "Nah save monet tday sadge"]
        await inter.response.send_message(
            f"<@{inter.author.id}> {random.choice(results)}"
        )

    @commands.slash_command(
        name="fubu",
        description="fubu",
    )
    async def fubu(self, inter: ApplicationCommandInteraction) -> None:
        """fubu"""
        await inter.response.defer()
        await inter.edit_original_message(**await general_helper.fubu())

    @commands.slash_command(
        name="holo",
        description="all live hololive streams",
    )
    async def holo(self, inter: ApplicationCommandInteraction) -> None:
        """all live hololive streams"""
        await inter.response.defer()
        await inter.edit_original_message(**await general_helper.holo())


class GeneralAdmin(commands.Cog):
    """bot admin commands"""

    COG_EMOJI = "📃"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.slash_command(
        name="set-prefix",
        description="set prefix for the server",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def set_prefix(
        self,
        inter: ApplicationCommandInteraction,
        prefix: str | None = None,
    ) -> None:
        """set prefix for the server"""
        await inter.response.defer()
        await inter.edit_original_message(
            **await general_helper.set_prefix(self.bot, inter, prefix)
        )


def setup(bot: commands.Bot) -> None:
    """loads general cog into bot"""
    bot.add_cog(General(bot))
    bot.add_cog(GeneralAdmin(bot))
