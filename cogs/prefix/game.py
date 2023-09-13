"""prefix commands for game related commands"""
from typing import Optional, Union

import disnake
from disnake.ext import commands

from helpers import valorant


class Valorant(commands.Cog, name="valorant"):
    """valorant related commands"""

    COG_EMOJI: str = "🕹️"

    @commands.command(
        name="valorant-ping",
        aliases=["valorantping", "valping", "vping", "jewels"],
        description="pings the role set for the guild",
    )
    @commands.guild_only()
    async def valorant_ping(self, ctx: commands.Context) -> None:
        """pings the role set for the guild
        and optionally sends a custom image"""
        await ctx.reply(**await valorant.ping(ctx))

    @commands.command(
        name="valorant-info",
        aliases=["valorantinfo", "valinfo", "vinfo"],
        description="retrieves the user's valorant info from the database",
    )
    async def valorant_info(
        self,
        ctx: commands.Context,
        user: Optional[disnake.User] = None,
    ) -> None:
        """retrieves the user's valorant info from the database

        if no user is specified, the author of the message is used

        parameters
        ----------
        user: Optional[disnake.User]
            the user to retrieve valorant info from, defaults to author
        """
        await ctx.reply(**await valorant.info(ctx, user))

    @commands.command(
        name="valorant-watch",
        aliases=["valorantwatch", "valwatch", "vwatch"],
        description="adds user's valorant info to the database",
    )
    async def valorant_watch(
        self,
        ctx: commands.Context,
        name: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> None:
        """adds user's valorant info to the database

        parameters
        ----------
        name: str
            the valorant username of the user
        tag: str
            the valorant tag of the user

        example
        -------
        >>> valorant-watch GuessJewels peko
        """
        if name is None:
            content: str = f"use {ctx.prefix}valorant-watch <name> <tag>"
            await ctx.reply(content=content)
            return
        if tag is None:
            if "#" not in name:
                content: str = f"use {ctx.prefix}valorant-watch <name> <tag>"
                await ctx.reply(content=content)
                return
            name, tag = name.split("#")[:2]
        message: disnake.Message = await ctx.reply(
            content="retrieving data..."
        )
        async with ctx.typing():
            await message.edit(**await valorant.watch(ctx, name, tag))

    @commands.command(
        name="valorant-unwatch",
        aliases=["valorantunwatch", "valunwatch", "vunwatch"],
        description="removes user's valorant info from the database",
    )
    async def valorant_unwatch(self, ctx: commands.Context) -> None:
        """removes user's valorant info from the database"""
        await ctx.reply(**await valorant.unwatch(ctx))

    @commands.command(
        name="valorant-wait",
        aliases=["valorantwait", "valwait", "vwait"],
        description="pings you when tagged users complete their game",
    )
    async def valorant_wait(
        self,
        ctx: commands.Context,
        *wait_users: disnake.User,
    ) -> None:
        """pings you when tagged users complete their game

        allows multiple users to be tagged

        parameters
        ----------
        wait_users: disnake.User
            the users to wait for to complete their game

        example
        -------
        >>> valorant-wait @user1 @user2
        """
        await ctx.reply(**await valorant.wait(ctx, *wait_users))

    @commands.command(
        name="valorant-waitlist",
        aliases=["valorantwaitlist", "valwaitlist", "vwaitlist"],
        description="shows users you are waiting for,"
        + " and users waiting for you",
    )
    async def valorant_waitlist(self, ctx: commands.Context) -> None:
        """shows users you are waiting for, and users waiting for you

        if sent in a guild, show the waitlist of users you are waiting for
        whose guild is the same as the current guild

        else if sent in a DM, show the waitlist of all users you are waiting
        for but the waiters for each user is hidden for privacy
        """
        await ctx.reply(**await valorant.waitlist(ctx))


class ValorantAdmin(commands.Cog, name="valorant admin"):
    """valorant admin commands"""

    COG_EMOJI: str = "🎮"

    @commands.command(
        name="set-channel",
        aliases=["setchannel"],
        description="sets the channel for the guild to send alerts to",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def set_channel(
        self,
        ctx: commands.Context,
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
        await ctx.reply(**await valorant.set_channel(ctx, channel))

    @commands.command(
        name="set-role",
        aliases=["setrole"],
        description="sets the role for the guild for `valorant-ping` to ping",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def set_role(
        self,
        ctx: commands.Context,
        role: Optional[disnake.Role] = None,
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
        await ctx.reply(**await valorant.set_role(ctx, role))

    options: str = "options: add, show, delete"

    @commands.group(
        name="ping-image",
        aliases=["pingimage", "ping-img", "pingimg"],
        description="custom image to be sent for `valorant-ping`",
        invoke_without_command=True,
    )
    async def ping_image(self, ctx: commands.Context) -> None:
        """custom image to be sent for `valorant-ping`"""
        await ctx.reply(
            content="custom image to be sent for `valorant-ping`. "
            + self.options
        )

    @ping_image.command(
        name="add",
        description="adds a custom image for `valorant-ping` for the"
        + " guild into the database",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def ping_image_add(
        self, ctx: commands.Context, new_image: Optional[str] = None
    ) -> None:
        """adds a custom image for `valorant-ping` for the guild
        into the database

        url of custom image must be valid and no more than 100 characters

        parameters
        ----------
        new_image: str
            the url of the custom image to add

        example
        -------
        >>> ping-image add https://example.com/image.png
        """
        if new_image is None:
            await ctx.reply(content=f'use {ctx.prefix}ping-image add "<url>"')
            return
        await ctx.reply(**await valorant.ping_image_add(ctx, new_image))

    @ping_image.command(
        name="show",
        description="shows the custom image for `valorant-ping` for the"
        + " guild if set",
    )
    async def ping_image_show(self, ctx: commands.Context) -> None:
        """shows the custom image for `valorant-ping` for the guild if set"""
        await ctx.reply(**await valorant.ping_image_show(ctx))

    @ping_image.command(
        name="delete",
        aliases=["del", "remove"],
        description="deletes the custom image for `valorant-ping` for the"
        + " guild if set",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def ping_image_delete(self, ctx: commands.Context) -> None:
        """deletes the custom image for `valorant-ping` for the guild if set"""
        await ctx.reply(**await valorant.ping_image_delete(ctx))

    @commands.group(
        name="feeder-message",
        aliases=["feedermessage", "feeder-msg", "feedermsg"],
        description="custom feeder alert messages sent in the watch alert",
        invoke_without_command=True,
    )
    async def feeder_message(self, ctx: commands.Context) -> None:
        """custom feeder alert messages sent in the watch alert"""
        await ctx.reply(
            content="custom feeder alert messages sent in the watch alert. "
            + self.options
        )

    @feeder_message.command(
        name="add",
        description="adds a custom feeder alert message"
        + " for the guild into the database",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_message_add(
        self, ctx: commands.Context, new_message: Optional[str] = None
    ) -> None:
        """adds a custom feeder alert message for the guild
        into the database

        message must be no more than 100 characters
        and total number of messages must not exceed 25

        parameters
        ----------
        new_message: str
            the custom message to add

        example
        -------
        >>> feeder-message add <message>
        """
        if new_message is None:
            await ctx.reply(
                content=f'use {ctx.prefix}feeder-message add "<message>"'
            )
            return
        await ctx.reply(**await valorant.feeder_message_add(ctx, new_message))

    @feeder_message.command(
        name="show",
        description="shows the custom feeder alert messages for the"
        + " guild if set",
    )
    async def feeder_message_show(self, ctx: commands.Context) -> None:
        """shows the custom feeder alert messages for the guild if set"""
        await ctx.reply(**await valorant.feeder_message_show(ctx))

    @feeder_message.command(
        name="delete",
        aliases=["del", "remove"],
        description="deletes custom feeder alert messages for the"
        + " guild from the database",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_message_delete(self, ctx: commands.Context) -> None:
        """deletes custom feeder alert messages for the guild
        from the database"""
        await ctx.reply(**await valorant.feeder_message_delete(ctx))

    @commands.group(
        name="feeder-image",
        aliases=["feederimage", "feeder-img", "feederimg"],
        description="custom feeder alert images sent in the watch alert",
        invoke_without_command=True,
    )
    async def feeder_image(self, ctx: commands.Context) -> None:
        """custom feeder alert images sent in the watch alert"""
        await ctx.reply(
            content="custom feeder alert images sent in the watch alert. "
            + self.options
        )

    @feeder_image.command(
        name="add",
        description="adds a custom feeder alert image"
        + " for the guild into the database",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_image_add(
        self, ctx: commands.Context, new_image: Optional[str] = None
    ) -> None:
        """adds a custom feeder alert image for the guild
        into the database

        url of custom image must be valid and no more than 100 characters
        and total number of images must not exceed 10

        parameters
        ----------
        new_image: str
            the url of the custom image to add

        example
        -------
        >>> feeder-image add https://example.com/image.png
        """
        if new_image is None:
            await ctx.reply(
                content=f'use {ctx.prefix}feeder-image add "<url>"'
            )
            return
        await ctx.reply(**await valorant.feeder_image_add(ctx, new_image))

    @feeder_image.command(
        name="show",
        description="shows the custom feeder alert images for the"
        + " guild if set",
    )
    async def feeder_image_show(self, ctx: commands.Context) -> None:
        """shows the custom feeder alert images for the guild if set"""
        await ctx.reply(**await valorant.feeder_image_show(ctx))

    @feeder_image.command(
        name="delete",
        aliases=["del", "remove"],
        description="deletes custom feeder alert images for the"
        + " guild from the database",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_image_delete(self, ctx: commands.Context) -> None:
        """deletes custom feeder alert images for the guild
        from the database"""
        await ctx.reply(**await valorant.feeder_image_delete(ctx))

    @commands.group(
        name="streaker-message",
        aliases=["streakermessage", "streaker-msg", "streakermsg"],
        description="custom streaker alert messages sent in the watch alert",
        invoke_without_command=True,
    )
    async def streaker_message(self, ctx: commands.Context) -> None:
        """custom streaker alert messages sent in the watch alert"""
        await ctx.reply(
            content="custom streaker alert messages sent in the watch alert. "
            + self.options
        )

    @streaker_message.command(
        name="add",
        description="adds a custom streaker alert message"
        + " for the guild into the database",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def streaker_message_add(
        self, ctx: commands.Context, new_message: Optional[str] = None
    ) -> None:
        """adds a custom streaker alert message for the guild
        into the database

        message must be no more than 100 characters
        and total number of messages must not exceed 25

        parameters
        ----------
        new_message: str
            the custom message to add

        example
        -------
        >>> streaker-message add <message>
        """
        if new_message is None:
            await ctx.reply(
                content=f'use {ctx.prefix}streaker-message add "<message>"'
            )
            return
        await ctx.reply(
            **await valorant.streaker_message_add(ctx, new_message)
        )

    @streaker_message.command(
        name="show",
        description="shows the custom streaker alert messages for the"
        + " guild if set",
    )
    async def streaker_message_show(self, ctx: commands.Context) -> None:
        """shows the custom streaker alert images for the guild if set"""
        await ctx.reply(**await valorant.streaker_message_show(ctx))

    @streaker_message.command(
        name="delete",
        aliases=["del", "remove"],
        description="deletes custom feeder alert images for the"
        + " guild from the database",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def streaker_message_delete(self, ctx: commands.Context) -> None:
        """deletes custom streaker alert images for the guild
        from the database"""
        await ctx.reply(**await valorant.streaker_message_delete(ctx))


def setup(bot: commands.Bot) -> None:
    """loads game cog into bot"""
    bot.add_cog(Valorant())
    bot.add_cog(ValorantAdmin())
