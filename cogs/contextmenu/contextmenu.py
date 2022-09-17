import disnake
from disnake.ext import commands

from helpers import valorant_helper


class ContextMenu(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.user_command(name="avatar")
    async def avatar(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User,
    ):
        """displays the user's avatar in an embed"""
        embed = disnake.Embed(title=f"{user}'s avatar")
        embed.set_image(url=user.display_avatar.url)
        await inter.response.send_message(embed=embed)

    @commands.user_command(name="valorant-wait")
    async def valorant_wait(
        self,
        inter: disnake.ApplicationCommandInteraction,
        wait_user: disnake.User,
    ):
        """pings you when tagged user is done"""
        await inter.response.defer()
        content = await valorant_helper.wait(self.bot, inter, wait_user)
        await inter.edit_original_message(content=content)


def setup(bot: commands.Bot):
    bot.add_cog(ContextMenu(bot))
