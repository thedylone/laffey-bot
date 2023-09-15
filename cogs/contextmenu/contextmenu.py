"""context menu commands"""
from disnake import ApplicationCommandInteraction, Embed, User
from disnake.ext import commands

from helpers import valorant


class ContextMenu(commands.Cog):
    """context menu commands

    functions that can be called when right clicking on a user

    attributes
    ----------
    bot: disnake.ext.commands.Bot
        bot instance
    """

    def __init__(self, bot: commands.Bot) -> None:
        """initialises the ContextMenu cog with the bot instance

        parameters
        ----------
        bot: disnake.ext.commands.Bot
            bot instance
        """
        self.bot: commands.Bot = bot
        """bot instance"""

    @commands.user_command(name="avatar")
    async def avatar(
        self,
        inter: ApplicationCommandInteraction,
        user: User,
    ) -> None:
        """responds to the interaction with the embed containing the user's
        avatar

        parameters
        ----------
        inter: disnake.ApplicationCommandInteraction
            interaction instance to respond to
        user: disnake.User
            user to display avatar of
        """
        embed = Embed(title=f"{user}'s avatar")
        embed.set_image(url=user.display_avatar.url)
        await inter.response.send_message(embed=embed)

    @commands.user_command(name="valorant-info")
    async def valorant_info(
        self, inter: ApplicationCommandInteraction, user: User
    ) -> None:
        """responds to the interaction with the embed containing the user's
        valorant info

        parameters
        ----------
        inter: disnake.ApplicationCommandInteraction
            interaction instance to respond to
        user: disnake.User
            user to display valorant info of
        """
        await inter.response.defer()
        await inter.edit_original_message(**await valorant.info(inter, user))

    @commands.user_command(name="valorant-wait")
    async def valorant_wait(
        self,
        inter: ApplicationCommandInteraction,
        wait_user: User,
    ) -> None:
        """adds the message author to the list of users waiting for the user

        parameters
        ----------
        inter: disnake.ApplicationCommandInteraction
            interaction instance to respond to
        wait_user: disnake.User
            user to wait for
        """
        await inter.response.defer()
        await inter.edit_original_message(
            **await valorant.wait(inter, wait_user)
        )


def setup(bot: commands.Bot) -> None:
    """loads context menu cog into bot"""
    bot.add_cog(ContextMenu(bot))
