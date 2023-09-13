"""slash commands for game related commands"""
from enum import Enum
from typing import Optional, Union

import disnake
from disnake.ext import commands

from helpers import valorant
from modals.modals import (
    FeederImageModal,
    FeederMessageModal,
    StreakerMessageModal,
    ValorantPingImageModal,
    ValorantWatchModal,
)


class Valorant(commands.Cog):
    """valorant related commands"""

    COG_EMOJI: str = "🕹️"

    @commands.slash_command(
        name="valorant-info",
        description="retrieves the user's valorant info from the database",
    )
    async def valorant_info(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: Optional[disnake.User] = None,
    ) -> None:
        """retrieves the user's valorant info from the database

        if no user is specified, the author of the message is used

        parameters
        ----------
        user: Optional[disnake.User]
            the user to retrieve valorant info from, defaults to author
        """
        await inter.response.defer()
        await inter.edit_original_message(**await valorant.info(inter, user))

    @commands.slash_command(
        name="valorant-watch",
        description="adds user's valorant info to the database",
    )
    async def valorant_watch(
        self, inter: disnake.ApplicationCommandInteraction
    ) -> None:
        """adds user's valorant info to the database

        sends a modal to the user to input their valorant info
        """
        await inter.response.send_modal(modal=ValorantWatchModal())

    @commands.slash_command(
        name="valorant-unwatch",
        description="removes user's valorant info from the database",
    )
    async def valorant_unwatch(
        self, inter: disnake.ApplicationCommandInteraction
    ) -> None:
        """removes user's valorant info from the database"""
        await inter.response.defer()
        await inter.edit_original_message(**await valorant.unwatch(inter))

    @commands.slash_command(
        name="valorant-wait",
        description="pings you when tagged user complete their game",
    )
    async def valorant_wait(
        self,
        inter: disnake.ApplicationCommandInteraction,
        wait_user: disnake.User,
    ) -> None:
        """pings you when tagged user complete their game

        parameters
        ----------
        wait_user: disnake.User
            the user to wait for to complete their game
        """
        await inter.response.defer()
        await inter.edit_original_message(
            **await valorant.wait(inter, wait_user)
        )

    @commands.slash_command(
        name="valorant-waitlist",
        description="shows users you are waiting for,"
        + " and users waiting for you",
    )
    async def valorant_waitlist(
        self, inter: disnake.ApplicationCommandInteraction
    ) -> None:
        """shows users you are waiting for, and users waiting for you

        if sent in a guild, show the waitlist of users you are waiting for
        whose guild is the same as the current guild

        else if sent in a DM, show the waitlist of all users you are waiting
        for but the waiters for each user is hidden for privacy
        """
        await inter.response.defer()
        await inter.edit_original_message(**await valorant.waitlist(inter))


class ValorantAdmin(commands.Cog):
    """valorant admin commands"""

    COG_EMOJI: str = "🎮"

    @commands.slash_command(
        name="set-channel",
        description="sets the channel for the guild to send alerts to",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def set_channel(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: Optional[
            Union[disnake.TextChannel, disnake.VoiceChannel, disnake.Thread]
        ] = None,
    ) -> None:
        """sets the channel for the guild to send alerts to

        if no channel is specified, the channel the message was sent in is used

        parameters
        ----------
        channel: Optional[Union[disnake.TextChannel, disnake.VoiceChannel,
        disnake.Thread]]
            the channel to send alerts to (default: the channel the message
            was sent in)

        example
        -------
        >>> set-channel #valorant
        """
        await inter.response.defer()
        await inter.edit_original_message(
            **await valorant.set_channel(inter, channel)
        )

    @commands.slash_command(
        name="set-role",
        description="sets the role for the guild for `valorant-ping` to ping",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def set_role(
        self,
        inter: disnake.ApplicationCommandInteraction,
        role: disnake.Role,
    ) -> None:
        """sets the role for the guild for `valorant-ping` to ping

        parameters
        ----------
        role: disnake.Role
            the role to ping for `valorant-ping`

        example
        -------
        >>> set-role @Valorant
        """
        await inter.response.defer()
        await inter.edit_original_message(
            **await valorant.set_role(inter, role)
        )

    class CustomOptions(str, Enum):
        """customise options"""

        ADD = "add"
        SHOW = "show"
        DELETE = "delete"

    @commands.slash_command(
        name="ping-image",
        description="custom image to be sent for `valorant-ping`",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def ping_image(
        self,
        inter: disnake.ApplicationCommandInteraction,
        option: CustomOptions,
    ) -> None:
        """custom image to be sent for `valorant-ping`

        parameters
        ----------
        option: CustomOptions
            the option to perform
        """
        if option == "add":
            await inter.response.send_modal(modal=ValorantPingImageModal())
        elif option == "show":
            await inter.response.defer()
            await inter.edit_original_message(
                **await valorant.ping_image_show(inter)
            )
        elif option == "delete":
            await inter.response.defer()
            await inter.edit_original_message(
                **await valorant.ping_image_delete(inter)
            )
        else:
            await inter.response.send_message(
                content="use /ping-image <add | show | delete>"
            )

    @commands.slash_command(
        name="feeder-message",
        description="custom feeder alert messages sent in the watch alert",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_message(
        self,
        inter: disnake.ApplicationCommandInteraction,
        option: CustomOptions,
    ) -> None:
        """custom feeder alert messages sent in the watch alert

        parameters
        ----------
        option: CustomOptions
            the option to perform
        """
        if option == "add":
            await inter.response.send_modal(modal=FeederMessageModal())
        elif option == "show":
            await inter.response.defer()
            await inter.edit_original_message(
                **await valorant.feeder_message_show(inter)
            )
        elif option == "delete":
            await inter.response.defer()
            await inter.edit_original_message(
                **await valorant.feeder_message_delete(inter)
            )
        else:
            await inter.response.send_message(
                content="use /feeder-message <add | show | delete>"
            )

    @commands.slash_command(
        name="feeder-image",
        description="custom feeder alert images sent in the watch alert",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_image(
        self,
        inter: disnake.ApplicationCommandInteraction,
        option: CustomOptions,
    ) -> None:
        """custom feeder alert images sent in the watch alert

        parameters
        ----------
        option: CustomOptions
            the option to perform
        """
        if option == "add":
            await inter.response.send_modal(modal=FeederImageModal())
        elif option == "show":
            await inter.response.defer()
            await inter.edit_original_message(
                **await valorant.feeder_image_show(inter)
            )
        elif option == "delete":
            await inter.response.defer()
            await inter.edit_original_message(
                **await valorant.feeder_image_delete(inter)
            )
        else:
            await inter.response.send_message(
                content="use /feeder-image <add | show | delete>"
            )

    @commands.slash_command(
        name="streaker-message",
        description="custom streaker alert messages sent in the watch alert",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def streaker_message(
        self,
        inter: disnake.ApplicationCommandInteraction,
        option: CustomOptions,
    ) -> None:
        """custom streaker alert messages sent in the watch alert

        parameters
        ----------
        option: CustomOptions
            the option to perform
        """
        if option == "add":
            await inter.response.send_modal(modal=StreakerMessageModal())
        elif option == "show":
            await inter.response.defer()
            await inter.edit_original_message(
                **await valorant.streaker_message_show(inter)
            )
        elif option == "delete":
            await inter.edit_original_message(
                **await valorant.streaker_message_delete(inter)
            )
        else:
            await inter.response.send_message(
                content="use /streaker-message <add | show | delete>"
            )


def setup(bot: commands.Bot) -> None:
    """loads game cog into bot"""
    bot.add_cog(Valorant())
    bot.add_cog(ValorantAdmin())
