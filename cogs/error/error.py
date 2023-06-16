"""handles errors for the bot"""

from disnake.ext import commands


class ErrorHandler(commands.Cog):
    """A cog for global error handling."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_command_error(
        self,
        ctx: commands.Context,
        error: commands.CommandError,
    ) -> None:
        """A global error handler cog."""
        if isinstance(error, commands.CommandNotFound):
            # Return because we don't want to show for every command not found
            return
        if isinstance(error, commands.CommandOnCooldown):
            cooldown: str = (
                f"Try again after {round(error.retry_after, 1)} seconds"
            )
            message: str = f"This command is on cooldown. {cooldown}."
        elif isinstance(error, commands.MissingPermissions):
            message = "You don't have the permissions to run this command!"
        elif isinstance(error, commands.UserInputError):
            message = "Your input was wrong, please check and try again!"
        elif isinstance(error, commands.NoPrivateMessage):
            message = "This command cannot be run in a Private Message!"
        else:
            message = "Oh no! Something went wrong while running the command!"

        await ctx.send(message)


def setup(bot: commands.Bot) -> None:
    """loads error handler cog into bot"""
    bot.add_cog(ErrorHandler(bot))
