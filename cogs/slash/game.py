"""slash commands for game related commands"""

from enum import Enum
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

    COG_EMOJI: str = "🕹️"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.slash_command(
        name="valorant-info",
        description="view valorant data in database",
    )
    async def valorant_info(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User | None = None,
    ) -> None:
        """returns user's valorant info from the database"""
        await inter.response.defer()
        await inter.edit_original_message(
            **await valorant_helper.info(self.bot, inter, user)
        )

    @commands.slash_command(
        name="valorant-watch",
        description="adds user into database",
    )
    async def valorant_watch(
        self, inter: disnake.ApplicationCommandInteraction
    ) -> None:
        """add user's valorant info to the database"""
        await inter.response.send_modal(modal=ValorantWatchModal(self.bot))

    @commands.slash_command(
        name="valorant-unwatch",
        description="removes user's valorant info from the database",
    )
    async def valorant_unwatch(
        self, inter: disnake.ApplicationCommandInteraction
    ) -> None:
        """removes user's valorant info from the database"""
        await inter.response.defer()
        await inter.edit_original_message(
            **await valorant_helper.unwatch(self.bot, inter)
        )

    @commands.slash_command(
        name="valorant-wait",
        description="pings you when tagged user is done",
    )
    async def valorant_wait(
        self,
        inter: disnake.ApplicationCommandInteraction,
        wait_user: disnake.User,
    ) -> None:
        """pings you when tagged user is done"""
        await inter.response.defer()
        await inter.edit_original_message(
            **await valorant_helper.wait(self.bot, inter, wait_user)
        )

    @commands.slash_command(
        name="valorant-waitlist",
        description="prints valorant waitlist",
    )
    async def valorant_waitlist(
        self, inter: disnake.ApplicationCommandInteraction
    ) -> None:
        """prints valorant waitlist"""
        await inter.response.defer()
        await inter.edit_original_message(
            **await valorant_helper.waitlist(self.bot, inter)
        )


class ValorantAdmin(commands.Cog):
    """valorant admin commands"""

    COG_EMOJI: str = "🎮"

    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.slash_command(
        name="set-channel",
        description="set the channel the bot will send updates to",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def set_channel(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel
        | disnake.VoiceChannel
        | disnake.Thread
        | None = None,
    ) -> None:
        """set the channel the bot will send updates to"""
        await inter.response.defer()
        await inter.edit_original_message(
            **await valorant_helper.set_channel(self.bot, inter, channel)
        )

    @commands.slash_command(
        name="set-role",
        description="set the role the bot will ping",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def set_role(
        self,
        inter: disnake.ApplicationCommandInteraction,
        role: disnake.Role,
    ) -> None:
        "set the role the bot will ping"
        await inter.response.defer()
        await inter.edit_original_message(
            **await valorant_helper.set_role(self.bot, inter, role)
        )

    class CustomOptions(str, Enum):
        """customise options"""

        ADD = "add"
        SHOW = "show"
        DELETE = "delete"

    @commands.slash_command(
        name="ping-image",
        description="custom image for ping alert functions",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def ping_image(
        self,
        inter: disnake.ApplicationCommandInteraction,
        option: CustomOptions,
    ) -> None:
        """custom ping images functions"""
        if option == "add":
            await inter.response.send_modal(
                modal=ValorantPingImageModal(self.bot)
            )
        elif option == "show":
            await inter.response.defer()
            await inter.edit_original_message(
                **await valorant_helper.ping_image_show(self.bot, inter)
            )
        elif option == "delete":
            await inter.response.defer()
            await inter.edit_original_message(
                **await valorant_helper.ping_image_delete(self.bot, inter)
            )
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
        option: CustomOptions,
    ) -> None:
        """custom feeder messages functions"""
        if option == "add":
            await inter.response.send_modal(
                modal=ValorantFeederMessageModal(self.bot)
            )
        elif option == "show":
            await inter.response.defer()
            await inter.edit_original_message(
                **await valorant_helper.feeder_message_show(self.bot, inter)
            )
        elif option == "delete":
            await inter.response.defer()
            await inter.edit_original_message(
                **await valorant_helper.feeder_message_delete(self.bot, inter)
            )
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
        option: CustomOptions,
    ) -> None:
        """custom feeder images functions"""
        if option == "add":
            await inter.response.send_modal(
                modal=ValorantFeederImageModal(self.bot)
            )
        elif option == "show":
            await inter.response.defer()
            await inter.edit_original_message(
                **await valorant_helper.feeder_image_show(self.bot, inter)
            )
        elif option == "delete":
            await inter.response.defer()
            await inter.edit_original_message(
                **await valorant_helper.feeder_image_delete(self.bot, inter)
            )
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
        option: CustomOptions,
    ) -> None:
        """custom streaker messages functions"""
        if option == "add":
            await inter.response.send_modal(
                modal=ValorantStreakerMessageModal(self.bot)
            )
        elif option == "show":
            await inter.response.defer()
            await inter.edit_original_message(
                **await valorant_helper.streaker_message_show(self.bot, inter)
            )
        elif option == "delete":
            await inter.edit_original_message(
                **await valorant_helper.streaker_message_delete(
                    self.bot, inter
                )
            )
        else:
            await inter.response.send_message(
                content="use /streaker-message <add | show | delete>"
            )


def setup(bot: commands.Bot) -> None:
    """loads game cog into bot"""
    bot.add_cog(Valorant(bot))
    bot.add_cog(ValorantAdmin(bot))
