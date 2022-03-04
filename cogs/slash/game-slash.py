import disnake
from disnake.ext import commands

import os
import json
import sys

from helpers import json_helper
from modals.modals import valorant_watch_modal

# RIOT_TOKEN = os.environ["RIOT_TOKEN"] not used at the moment

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found!")
else:
    with open("config.json", encoding="utf-8") as file:
        config = json.load(file)


class Game(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="jewels", description="pings role")
    async def jewels_ping(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        """pings @jewels role and sends image"""
        await inter.edit_original_message(
            content=f"<@&{config['ping_role']}>", file=disnake.File("jewelsignal.jpg")
        )

    @commands.slash_command(
        name="valorant-info", description="view valorant data in database"
    )
    async def valorant_info(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        """returns user's valorant info from the database"""
        player_data = json_helper.load("playerData.json")
        user_id = str(inter.user.id)
        if user_id in player_data:
            user_data = player_data[user_id]
            embed = disnake.Embed(
                title="valorant info", description=f"<@{user_id}> saved info"
            )
            embed.set_thumbnail(url=inter.user.display_avatar.url)
            embed.add_field(name="username", value=f"{user_data['name']}", inline=True)
            embed.add_field(name="tag", value=f"#{user_data['tag']}", inline=True)
            embed.add_field(
                name="last updated", value=f"<t:{int(user_data['lastTime'])}>"
            )
            await inter.edit_original_message(embed=embed)
        else:
            await inter.edit_original_message(
                content=f"<@{user_id}> not in database! do /valorant-watch first"
            )

    @commands.slash_command(
        name="valorant-watch", description="adds user into database"
    )
    async def valorant_watch(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_modal(modal=valorant_watch_modal())

    @commands.slash_command(
        name="valorant-unwatch",
        description="removes user's valorant info from the database",
    )
    async def valorant_unwatch(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        """removes user's valorant info from the database"""
        player_data = json_helper.load("playerData.json")
        user_id = str(inter.user.id)
        if user_id in player_data:
            del player_data[user_id]
            json_helper.save(player_data, "playerData.json")
            await inter.edit_original_message(
                content=f"<@{user_id}> database updated, user removed. add again using /valorant-watch"
            )
        else:
            await inter.edit_original_message(
                content=f"<@{user_id}> error updating, user not in database"
            )

    @commands.slash_command(
        name="valorant-wait", description="pings you when tagged user is done"
    )
    async def valorant_wait(
        self, inter: disnake.ApplicationCommandInteraction, wait_user: disnake.User
    ):
        await inter.response.defer()
        """pings you when tagged user is done"""
        player_data = json_helper.load("playerData.json")
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

    @commands.slash_command(
        name="valorant-waitlist", description="prints valorant waitlist"
    )
    async def valorant_waitlist(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        """prints valorant waitlist"""
        embed = disnake.Embed(
            title="valorant waitlist", description="waitlist of watched users"
        )
        embed.set_thumbnail(
            url="https://cdn.vox-cdn.com/uploads/chorus_image/image/66615355/VALORANT_Jett_Red_crop.0.jpg"
        )
        for user_id in self.bot.valorant_waitlist:
            embed.add_field(name="user", value=f"<@{user_id}>", inline=False)
            embed.add_field(
                name="waiters",
                value=f"<@{'> <@'.join(self.bot.valorant_waitlist[user_id])}>",
            )
        await inter.edit_original_message(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Game(bot))
