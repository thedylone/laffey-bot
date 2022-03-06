import disnake
from disnake.ext import commands

import os
import json
import sys

from helpers import json_helper
from modals.modals import ValorantWatchModal

# RIOT_TOKEN = os.environ["RIOT_TOKEN"] not used at the moment

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found!")
else:
    with open("config.json", encoding="utf-8") as file:
        config = json.load(file)


class Valorant(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="jewels", description="pings role")
    @commands.guild_only()
    async def jewels_ping(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        """pings @jewels role and sends image"""
        guild_id = inter.guild.id
        guild_data = json_helper.load("guildData.json")
        if "ping_role" not in guild_data[str(guild_id)]:
            await inter.edit_original_message(
                content="please set the role to ping first using valorant-setrole!"
            )
        else:
            ping_role = guild_data[str(guild_id)]["ping_role"]
            await inter.edit_original_message(
                content=f"<@&{ping_role}>", file=disnake.File("jewelsignal.jpg")
            )

    @commands.slash_command(
        name="valorant-info", description="view valorant data in database"
    )
    async def valorant_info(
        self, inter: disnake.ApplicationCommandInteraction, user: disnake.User = None
    ):
        await inter.response.defer()
        """returns user's valorant info from the database"""
        player_data = json_helper.load("playerData.json")
        if user == None:
            user = inter.user
        user_id = str(user.id)
        if user_id in player_data:
            user_data = player_data[user_id]
            embed = disnake.Embed(
                title="valorant info", description=f"<@{user_id}> saved info"
            )
            embed.set_thumbnail(url=user.display_avatar.url)
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
        if isinstance(inter.channel, disnake.channel.DMChannel):
            guild_id = 0
        else:
            guild_data = json_helper.load("guildData.json")
            guild_id = inter.guild_id
            if (
                str(guild_id) not in guild_data
                or "watch_channel" not in guild_data[str(guild_id)]
                or guild_data[str(guild_id)]["watch_channel"] == 0
            ):
                await inter.send(
                    content="Please set the watch channel for the guild first using valorant-setchannel! You can also DM me and I will DM you for each update instead!"
                )
                return
        await inter.response.send_modal(modal=ValorantWatchModal())

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


class ValorantAdmin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="valorant-setchannel",
        description="set the channel the bot will send updates to",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def valorant_setchannel(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        """set the channel the bot will send updates to"""
        channel = inter.channel
        guild = inter.guild
        guild_data = json_helper.load("guildData.json")
        guild_data[str(guild.id)]["watch_channel"] = channel.id
        json_helper.save(guild_data, "guildData.json")
        await inter.edit_original_message(
            content=f"Successfully set `#{channel}` as watch channel for `{guild}`"
        )

    @commands.slash_command(
        name="valorant-setrole",
        description="set the role the bot will ping",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def valorant_setrole(
        self, inter: disnake.ApplicationCommandInteraction, role: disnake.Role
    ):
        await inter.response.defer()
        "set the role the bot will ping"
        guild = inter.guild
        guild_data = json_helper.load("guildData.json")
        guild_data[str(guild.id)]["ping_role"] = role.id
        json_helper.save(guild_data, "guildData.json")
        await inter.edit_original_message(
            content=f"successfully set role `{role}` as watch channel for `{guild}`"
        )


def setup(bot: commands.Bot):
    bot.add_cog(Valorant(bot))
    bot.add_cog(ValorantAdmin(bot))
