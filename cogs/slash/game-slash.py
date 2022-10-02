import disnake
from disnake.ext import commands

from helpers import valorant_helper
from modals.modals import (
    ValorantWatchModal,
    ValorantPingImageModal,
    ValorantFeederMessageModal,
    ValorantFeederImageModal,
    ValorantStreakerMessageModal,
)


class Valorant(commands.Cog):
    """valorant related commands"""

    COG_EMOJI = "🕹️"

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="valorant-info",
        description="view valorant data in database",
    )
    async def valorant_info(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = None,
    ):
        """returns user's valorant info from the database"""
        await inter.response.defer()
        content, embed = await valorant_helper.info(self.bot, inter, user)
        await inter.edit_original_message(content=content, embed=embed)

    @commands.slash_command(
        name="valorant-watch",
        description="adds user into database",
    )
    async def valorant_watch(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        """add user's valorant info to the database"""
        await inter.response.send_modal(modal=ValorantWatchModal(self.bot))

    @commands.slash_command(
        name="valorant-unwatch",
        description="removes user's valorant info from the database",
    )
    async def valorant_unwatch(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        """removes user's valorant info from the database"""
        await inter.response.defer()
        content = await valorant_helper.unwatch(self.bot, inter)
        await inter.edit_original_message(content=content)

    @commands.slash_command(
        name="valorant-wait",
        description="pings you when tagged user is done",
    )
    async def valorant_wait(
        self,
        inter: disnake.ApplicationCommandInteraction,
        wait_user: disnake.User,
    ):
        """pings you when tagged user is done"""
        await inter.response.defer()
        content = await valorant_helper.wait(self.bot, inter, wait_user)
        await inter.edit_original_message(content=content)

    @commands.slash_command(
        name="valorant-waitlist",
        description="prints valorant waitlist",
    )
    async def valorant_waitlist(
        self, inter: disnake.ApplicationCommandInteraction
    ):
        """prints valorant waitlist"""
        await inter.response.defer()
        embed = await valorant_helper.waitlist(self.bot, inter)
        await inter.edit_original_message(embed=embed)


class ValorantAdmin(commands.Cog):
    """valorant admin commands"""

    COG_EMOJI = "🎮"

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(
        name="set-channel",
        description="set the channel the bot will send updates to",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def set_channel(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel = None,
    ):
        """set the channel the bot will send updates to"""
        await inter.response.defer()
        content = await valorant_helper.set_channel(self.bot, inter, channel)
        await inter.edit_original_message(content=content)

    @commands.slash_command(
        name="set-role",
        description="set the role the bot will ping",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def set_role(
        self,
        inter: disnake.ApplicationCommandInteraction,
        role: disnake.Role,
    ):
        "set the role the bot will ping"
        await inter.response.defer()
        content = await valorant_helper.set_role(self.bot, inter, role)
        await inter.edit_original_message(content=content)

    customise_options = commands.option_enum(["add", "show", "delete"])

    @commands.slash_command(
        name="ping-image",
        description="custom image for ping alert functions",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def ping_image(
        self,
        inter: disnake.ApplicationCommandInteraction,
        option: customise_options,
    ):
        """custom ping images functions"""
        if option == "add":
            await inter.response.send_modal(
                modal=ValorantPingImageModal(self.bot)
            )
        elif option == "show":
            await inter.response.defer()
            content, embed = await valorant_helper.ping_image_show(
                self.bot, inter
            )
            await inter.edit_original_message(content=content, embed=embed)
        elif option == "delete" or option == "del":
            await inter.response.defer()
            content = await valorant_helper.ping_image_delete(self.bot, inter)
            await inter.edit_original_message(content=content)
        else:
            await inter.response.send_message(
                content="use /ping-image <add | show | delete>"
            )

    @commands.slash_command(
        name="feeder-message",
        description="custom message for feeder alert functions",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_message(
        self,
        inter: disnake.ApplicationCommandInteraction,
        option: customise_options,
    ):
        """custom feeder messages functions"""
        if option == "add":
            await inter.response.send_modal(
                modal=ValorantFeederMessageModal(self.bot)
            )
        elif option == "show":
            await inter.response.defer()
            content, embed, view = await valorant_helper.feeder_message_show(
                self.bot, inter
            )
            await inter.edit_original_message(
                content=content, embed=embed, view=view
            )
        elif option == "delete" or option == "del":
            await inter.response.defer()
            content, view = await valorant_helper.feeder_message_delete(
                self.bot, inter
            )
            await inter.edit_original_message(content=content, view=view)
        else:
            await inter.response.send_message(
                content="use /feeder-message <add | show | delete>"
            )

    @commands.slash_command(
        name="feeder-image",
        description="custom image for feeder alert functions",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_image(
        self,
        inter: disnake.ApplicationCommandInteraction,
        option: customise_options,
    ):
        """custom feeder images functions"""
        if option == "add":
            await inter.response.send_modal(
                modal=ValorantFeederImageModal(self.bot)
            )
        elif option == "show":
            await inter.response.defer()
            content, embed, view = await valorant_helper.feeder_image_show(
                self.bot, inter
            )
            await inter.edit_original_message(
                content=content, embed=embed, view=view
            )
        elif option == "delete" or option == "del":
            await inter.response.defer()
            content, view = await valorant_helper.feeder_image_delete(
                self.bot, inter
            )
            await inter.edit_original_message(content=content, view=view)
        else:
            await inter.response.send_message(
                content="use /feeder-image <add | show | delete>"
            )

    @commands.slash_command(
        name="streaker-message",
        description="custom message for streaker alert functions",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def streaker_message(
        self,
        inter: disnake.ApplicationCommandInteraction,
        option: customise_options,
    ):
        """custom streaker messages functions"""
        if option == "add":
            await inter.response.send_modal(
                modal=ValorantStreakerMessageModal(self.bot)
            )
        elif option == "show":
            await inter.response.defer()
            content, embed, view = await valorant_helper.streaker_message_show(
                self.bot, inter
            )
            await inter.edit_original_message(
                content=content, embed=embed, view=view
            )
        elif option == "delete" or option == "del":
            await inter.response.defer()
            content, view = await valorant_helper.streaker_message_delete(
                self.bot, inter
            )
            await inter.edit_original_message(content=content, view=view)
        else:
            await inter.response.send_message(
                content="use /streaker-message <add | show | delete>"
            )


def setup(bot: commands.Bot):
    bot.add_cog(Valorant(bot))
    bot.add_cog(ValorantAdmin(bot))
