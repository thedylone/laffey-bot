import disnake
from disnake.ext import commands


from helpers import json_helper, valorant_helper
from modals.modals import (
    ValorantWatchModal,
    ValorantFeederMessageModal,
    ValorantFeederImageModal,
)

# RIOT_TOKEN = os.environ["RIOT_TOKEN"] not used at the moment


class Valorant(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="valorant-info", description="view valorant data in database"
    )
    async def valorant_info(
        self, inter: disnake.ApplicationCommandInteraction, user: disnake.User = None
    ):
        await inter.response.defer()
        """returns user's valorant info from the database"""
        content, embed = await valorant_helper.info(inter, user)
        await inter.edit_original_message(content=content, embed=embed)

    @commands.slash_command(
        name="valorant-watch", description="adds user into database"
    )
    async def valorant_watch(self, inter: disnake.ApplicationCommandInteraction):
        """add user's valorant info to the database"""
        await inter.response.send_modal(modal=ValorantWatchModal())

    @commands.slash_command(
        name="valorant-unwatch",
        description="removes user's valorant info from the database",
    )
    async def valorant_unwatch(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        """removes user's valorant info from the database"""
        content = await valorant_helper.unwatch(inter)
        await inter.edit_original_message(content=content)

    @commands.slash_command(
        name="valorant-wait", description="pings you when tagged user is done"
    )
    async def valorant_wait(
        self, inter: disnake.ApplicationCommandInteraction, wait_user: disnake.User
    ):
        await inter.response.defer()
        """pings you when tagged user is done"""
        content = await valorant_helper.wait(self.bot, inter, wait_user)
        await inter.edit_original_message(content=content)

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
        name="feeder-message",
        description="custom message for feeder alert functions",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_message(
        self, inter: disnake.ApplicationCommandInteraction, option: str
    ):
        """custom feeder messages functions"""
        if option == "add":
            await inter.response.send_modal(modal=ValorantFeederMessageModal())
        elif option == "show":
            await inter.response.defer()
            content, embed, view = await valorant_helper.feeder_message_show(inter)
            await inter.edit_original_message(content=content, embed=embed, view=view)
        elif option == "delete" or option == "del":
            await inter.response.defer()
            content, view = await valorant_helper.feeder_message_delete(inter)
            await inter.edit_original_message(content=content, view=view)
        else:
            await inter.response.send_message(
                content=f"use /feeder-message <add | show | delete>"
            )

    @feeder_message.autocomplete("option")
    async def feeder_message_autocomplete(
        self, inter: disnake.ApplicationCommandInteraction, string: str
    ):
        string = string.lower()
        return [
            option for option in ["add", "show", "delete"] if string in option.lower()
        ]

    @commands.slash_command(
        name="feeder-image",
        description="custom image for feeder alert functions",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_image(
        self, inter: disnake.ApplicationCommandInteraction, option: str
    ):
        """custom feeder images functions"""
        if option == "add":
            await inter.response.send_modal(modal=ValorantFeederImageModal())
        elif option == "show":
            await inter.response.defer()
            content, embed, view = await valorant_helper.feeder_image_show(inter)
            await inter.edit_original_message(content=content, embed=embed, view=view)
        elif option == "delete" or option == "del":
            await inter.response.defer()
            content, view = await valorant_helper.feeder_image_delete(inter)
            await inter.edit_original_message(content=content, view=view)
        else:
            await inter.response.send_message(
                content=f"use /feeder-image <add | show | delete>"
            )

    @feeder_image.autocomplete("option")
    async def feeder_image_autocomplete(
        self, inter: disnake.ApplicationCommandInteraction, string: str
    ):
        string = string.lower()
        return [
            option for option in ["add", "show", "delete"] if string in option.lower()
        ]


def setup(bot: commands.Bot):
    bot.add_cog(Valorant(bot))
    bot.add_cog(ValorantAdmin(bot))
