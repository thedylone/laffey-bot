"""context menu commands"""

from disnake import User, ApplicationCommandInteraction, Embed
from disnake.ext import commands

from helpers import valorant_helper


class ContextMenu(commands.Cog):
    """context menu commands"""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.user_command(name="avatar")
    async def avatar(
        self,
        inter: ApplicationCommandInteraction,
        user: User,
    ) -> None:
        """displays the user's avatar in an embed"""
        embed = Embed(title=f"{user}'s avatar")
        embed.set_image(url=user.display_avatar.url)
        await inter.response.send_message(embed=embed)

    @commands.user_command(name="valorant-info")
    async def valorant_info(
        self, inter: ApplicationCommandInteraction, user: User
    ) -> None:
        """returns user's valorant info from the database"""
        await inter.response.defer()
        await inter.edit_original_message(
            **await valorant_helper.info(self.bot, inter, user)
        )

    @commands.user_command(name="valorant-wait")
    async def valorant_wait(
        self,
        inter: ApplicationCommandInteraction,
        wait_user: User,
    ) -> None:
        """pings you when tagged user is done"""
        await inter.response.defer()
        await inter.edit_original_message(
            **await valorant_helper.wait(self.bot, inter, wait_user)
        )


def setup(bot: commands.Bot) -> None:
    """loads context menu cog into bot"""
    bot.add_cog(ContextMenu(bot))
