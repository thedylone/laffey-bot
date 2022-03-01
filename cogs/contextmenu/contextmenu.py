import disnake
from disnake.ext import commands

import os
import json
import sys

from helpers import json_helper

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found!")
else:
    with open("config.json", encoding="utf-8") as file:
        config = json.load(file)


class ContextMenu(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.user_command(name="avatar")
    async def avatar(
        self, inter: disnake.ApplicationCommandInteraction, user: disnake.User
    ):
        embed = disnake.Embed(title=f"{user}'s avatar")
        embed.set_image(url=user.display_avatar.url)
        await inter.response.send_message(embed=embed)

    @commands.user_command(name="valorant-wait")
    async def valorant_wait(
        self, inter: disnake.ApplicationCommandInteraction, wait_user: disnake.User
    ):
        await inter.response.defer()
        """pings you when tagged user is done"""
        player_data = json_helper.load()
        wait_user_id = str(wait_user.id)
        inter_user_id = str(inter.user.id)
        extra_message = ""
        if wait_user_id == inter_user_id:
            extra_message = "interesting but ok. "
        if wait_user_id in player_data:
            if wait_user_id in self.bot.valorant_waitlist:
                if inter_user_id in self.bot.valorant_waitlist[wait_user_id]:
                    await inter.edit_original_message(
                        content=f"{extra_message}<@{inter_user_id}> you are already waiting for <@{wait_user_id}>"
                    )
                    return
                else:
                    self.bot.valorant_waitlist[wait_user_id] += [inter_user_id]
            else:
                self.bot.valorant_waitlist[wait_user_id] = [inter_user_id]
            await inter.edit_original_message(
                content=f"{extra_message}<@{inter_user_id}> success, will notify when <@{wait_user_id}> is done"
            )
        else:
            await inter.edit_original_message(
                content=f"{extra_message}<@{wait_user_id}> is not in database, unable to execute"
            )


def setup(bot: commands.Bot):
    bot.add_cog(ContextMenu(bot))
