"""prefix commands for general commands"""
import random
from typing import Optional

from disnake import Message
from disnake.ext import commands

from helpers import general


class General(commands.Cog, name="general"):
    """miscellaneous bot commands"""

    COG_EMOJI = "🤖"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.command(
        name="ping",
        description="get the bot's current websocket latency",
    )
    async def ping(self, ctx: commands.Context) -> None:
        """get the bot's current websocket latency"""
        await ctx.reply(f"pong! {round(self.bot.latency * 1000)}ms")

    @commands.command(
        name="shouldiorder",
        description="should you get indulge?",
    )
    async def rng(self, ctx: commands.Context) -> None:
        """should you get indulge?"""
        results: list[str] = ["Hell yea boiii", "Nah save monet tday sadge"]
        await ctx.reply(f"<@{ctx.author.id}> {random.choice(results)}")

    @commands.command(
        name="fubu",
        description="fubu",
    )
    async def fubu(self, ctx: commands.Context) -> None:
        """fubu"""
        reply: Message = await ctx.reply("fetching streams...")
        async with ctx.typing():
            await reply.edit(**await general.fubu(reply=reply))

    @commands.command(
        name="holo",
        description="all live hololive streams",
    )
    async def holo(self, ctx: commands.Context) -> None:
        """all live hololive streams"""
        reply: Message = await ctx.reply("fetching streams...")
        async with ctx.typing():
            await reply.edit(**await general.holo(reply=reply))


class GeneralAdmin(commands.Cog, name="general admin"):
    """bot admin commands"""

    COG_EMOJI = "📃"

    @commands.command(
        name="set-prefix",
        description="set the prefix for the guild",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def set_prefix(
        self,
        ctx: commands.Context,
        prefix: Optional[str] = None,
    ) -> None:
        """set the prefix for the guild

        parameters
        ----------
        prefix: str
            the new prefix for the guild

        example
        -------
        >>> set-prefix !
        """
        await ctx.reply(**await general.set_prefix(ctx, prefix))


def setup(bot: commands.Bot) -> None:
    """loads general cog into bot"""
    bot.add_cog(General(bot))
    bot.add_cog(GeneralAdmin())
