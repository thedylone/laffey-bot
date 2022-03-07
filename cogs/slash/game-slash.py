import disnake
from disnake.ext import commands

import os
import json
import sys

from helpers import json_helper
from modals.modals import (
    ValorantWatchModal,
    ValorantFeederMessageModal,
    ValorantFeederImageModal,
)
from views.views import FeederImagesView, FeederMessagesView, Menu

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
                content="please set the role to ping first using valorant-set-role!"
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
                    content="Please set the watch channel for the guild first using valorant-set-channel! You can also DM me and I will DM you for each update instead!"
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
        if isinstance(inter.channel, disnake.channel.DMChannel):
            guild_id = 0
        else:
            guild_id = inter.guild.id
        player_data = json_helper.load("playerData.json")
        embed = disnake.Embed(
            title="valorant waitlist", description="waitlist of watched users"
        )
        embed.set_thumbnail(
            url="https://cdn.vox-cdn.com/uploads/chorus_image/image/66615355/VALORANT_Jett_Red_crop.0.jpg"
        )
        for user_id in self.bot.valorant_waitlist:
            if guild_id == 0 and inter.author.id in self.bot.valorant_waitlist[user_id]:
                embed.add_field(name="user", value=f"<@{user_id}>", inline=False)
                embed.add_field(
                    name="waiters",
                    value=f"<@{inter.author.id}>",
                )
            elif (
                user_id == str(inter.author.id)
                or guild_id
                and player_data[user_id]["guild"] == guild_id
            ):
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
        name="valorant-set-channel",
        description="set the channel the bot will send updates to",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def valorant_set_channel(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel = None,
    ):
        await inter.response.defer()
        """set the channel the bot will send updates to"""
        if channel == None:
            channel = inter.channel
        guild = inter.guild
        guild_data = json_helper.load("guildData.json")
        guild_data[str(guild.id)]["watch_channel"] = channel.id
        json_helper.save(guild_data, "guildData.json")
        await inter.edit_original_message(
            content=f"Successfully set `#{channel}` as watch channel for `{guild}`"
        )

    @commands.slash_command(
        name="valorant-set-role",
        description="set the role the bot will ping",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def valorant_set_role(
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

    @commands.slash_command(
        name="valorant-add-feeder-message",
        description="add custom message for feeder alert",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def valorant_add_feeder_message(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        """add custom message for feeder alert"""
        guild = inter.guild
        guild_data = json_helper.load("guildData.json")
        if (
            "feeder_messages" in guild_data[str(guild.id)]
            and len(guild_data[str(guild.id)]["feeder_messages"]) == 25
        ):
            await inter.response.send_message(
                content="max number of messages reached! delete one before adding a new one!"
            )
            return
        await inter.response.send_modal(modal=ValorantFeederMessageModal())

    @commands.slash_command(
        name="valorant-show-feeder-messages",
        description="show custom messages for feeder alert",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def valorant_show_feeder_message(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        await inter.response.defer()
        """show custom messages for feeder alert"""
        guild = inter.guild
        guild_data = json_helper.load("guildData.json")
        if (
            "feeder_messages" not in guild_data[str(guild.id)]
            or not guild_data[str(guild.id)]["feeder_messages"]
        ):
            await inter.edit_original_message(
                content=f'no custom messages for `{guild}`! add using /valorant-add-feeder-message "<custom message>"!'
            )
        else:
            feeder_messages = guild_data[str(guild.id)]["feeder_messages"]
            embeds = []
            step = 5  # number of messages per embed
            for i in range(0, len(feeder_messages), step):
                embed = disnake.Embed(
                    title="custom feeder messages",
                    description="messsages randomly sent with the feeder alert",
                )
                value = ""
                for j, message in enumerate(feeder_messages[i : i + step]):
                    value += f"`{i+j}` {message} \n"
                embed.add_field(name="messages", value=value)
                embeds.append(embed)
            if len(feeder_messages) > step:
                await inter.edit_original_message(embed=embeds[0], view=Menu(embeds))
            else:
                await inter.edit_original_message(embed=embeds[0])

    @commands.slash_command(
        name="valorant-delete-feeder-message",
        description="delete custom message for feeder alert",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def valorant_delete_feeder_message(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        await inter.response.defer()
        """delete custom message for feeder alert"""
        guild = inter.guild
        guild_data = json_helper.load("guildData.json")
        if (
            "feeder_messages" not in guild_data[str(guild.id)]
            or not guild_data[str(guild.id)]["feeder_messages"]
        ):
            await inter.edit_original_message(
                content=f'no custom messages for `{guild}`! add using /valorant-add-feeder-message "<custom message>"!'
            )
        else:
            view = FeederMessagesView(inter)
            await inter.edit_original_message(
                content="choose messages to delete", view=view
            )

    @commands.slash_command(
        name="valorant-add-feeder-image",
        description="add custom image for feeder alert",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def valorant_add_feeder_image(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        """add custom image for feeder alert"""
        guild = inter.guild
        guild_data = json_helper.load("guildData.json")
        if (
            "feeder_images" in guild_data[str(guild.id)]
            and len(guild_data[str(guild.id)]["feeder_images"]) == 10
        ):
            await inter.response.send_message(
                content="max number of images reached! delete one before adding a new one!"
            )
        else:
            await inter.response.send_modal(modal=ValorantFeederImageModal())

    @commands.slash_command(
        name="valorant-show-feeder-images",
        description="show custom images for feeder alert",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def valorant_show_feeder_image(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        await inter.response.defer()
        """show custom images for feeder alert"""
        guild = inter.guild
        guild_data = json_helper.load("guildData.json")
        if (
            "feeder_images" not in guild_data[str(guild.id)]
            or not guild_data[str(guild.id)]["feeder_images"]
        ):
            await inter.edit_original_message(
                content=f'no custom images for `{guild}`! add using /valorant-add-feeder-image "<custom image>"!'
            )
        else:
            feeder_images = guild_data[str(guild.id)]["feeder_images"]
            embeds = []
            for image in feeder_images:
                embed = disnake.Embed(
                    title="custom feeder images",
                    description="messsages randomly sent with the feeder alert",
                )
                embed.set_image(url=image)
                embeds.append(embed)
            if len(feeder_images) > 1:
                await inter.edit_original_message(embed=embeds[0], view=Menu(embeds))
            else:
                await inter.edit_original_message(embed=embeds[0])

    @commands.slash_command(
        name="valorant-delete-feeder-image",
        description="delete custom image for feeder alert",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def valorant_delete_feeder_image(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        await inter.response.defer()
        """delete custom image for feeder alert"""
        guild = inter.guild
        guild_data = json_helper.load("guildData.json")
        if (
            "feeder_images" not in guild_data[str(guild.id)]
            or not guild_data[str(guild.id)]["feeder_images"]
        ):
            await inter.edit_original_message(
                content=f'no custom images for `{guild}`! add using /valorant-add-feeder-image "<custom image>"!'
            )
        else:
            view = FeederImagesView(inter)
            await inter.edit_original_message(
                content="choose images to delete", view=view
            )


def setup(bot: commands.Bot):
    bot.add_cog(Valorant(bot))
    bot.add_cog(ValorantAdmin(bot))
