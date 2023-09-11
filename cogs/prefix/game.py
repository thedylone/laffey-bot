"""prefix commands for game related commands"""

from typing import Optional, Union
import disnake
from disnake.ext import commands

from helpers import valorant_helper


class Valorant(commands.Cog, name="valorant"):
    """valorant related commands"""

    COG_EMOJI: str = "🕹️"

    @commands.command(
        name="valorant-ping",
        aliases=["valorantping", "valping", "vping", "jewels"],
        description="pings role",
    )
    @commands.guild_only()
    async def valorant_ping(self, ctx: commands.Context) -> None:
        """pings role and sends optional image"""
        await ctx.send(**await valorant_helper.ping(ctx))

    @commands.command(
        name="valorant-info",
        aliases=["valorantinfo", "valinfo", "vinfo"],
        description="view valorant data in database",
    )
    async def valorant_info(
        self,
        ctx: commands.Context,
        user: Optional[disnake.User] = None,
    ) -> None:
        """returns user's valorant info from the database"""
        await ctx.send(**await valorant_helper.info(ctx, user))

    @commands.command(
        name="valorant-watch",
        aliases=["valorantwatch", "valwatch", "vwatch"],
        description="adds user into database",
    )
    async def valorant_watch(
        self,
        ctx: commands.Context,
        name: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> None:
        """add user's valorant info to the database.
        e.g. ?vwatch GuessJewels#peko"""
        if name is None:
            content: str = f"use {ctx.prefix}valorant-watch <name> <tag>"
            await ctx.send(content=content)
            return
        if tag is None:
            if "#" not in name:
                content: str = f"use {ctx.prefix}valorant-watch <name> <tag>"
                await ctx.send(content=content)
                return
            name, tag = name.split("#")[:2]
        message: disnake.Message = await ctx.send(content="retrieving data...")
        await message.edit(**await valorant_helper.watch(ctx, name, tag))

    @commands.command(
        name="valorant-unwatch",
        aliases=["valorantunwatch", "valunwatch", "vunwatch"],
        description="removes user's valorant info from the database",
    )
    async def valorant_unwatch(self, ctx: commands.Context) -> None:
        """removes user's valorant info from the database"""
        await ctx.send(**await valorant_helper.unwatch(ctx))

    @commands.command(
        name="valorant-wait",
        aliases=["valorantwait", "valwait", "vwait"],
        description="pings you when tagged user is done",
    )
    async def valorant_wait(
        self,
        ctx: commands.Context,
        *wait_users: disnake.User,
    ) -> None:
        """pings you when tagged user is done"""
        await ctx.send(**await valorant_helper.wait(ctx, *wait_users))

    @commands.command(
        name="valorant-waitlist",
        aliases=["valorantwaitlist", "valwaitlist", "vwaitlist"],
        description="prints valorant waitlist",
    )
    async def valorant_waitlist(self, ctx: commands.Context) -> None:
        """prints valorant waitlist"""
        await ctx.send(**await valorant_helper.waitlist(ctx))


class ValorantAdmin(commands.Cog, name="valorant admin"):
    """valorant admin commands"""

    COG_EMOJI: str = "🎮"

    @commands.command(
        name="set-channel",
        aliases=["setchannel"],
        description="set the channel the bot will send updates to",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def set_channel(
        self,
        ctx: commands.Context,
        channel: Optional[
            Union[disnake.TextChannel, disnake.VoiceChannel, disnake.Thread]
        ] = None,
    ) -> None:
        """set the channel the bot will send updates to"""
        await ctx.send(**await valorant_helper.set_channel(ctx, channel))

    @commands.command(
        name="set-role",
        aliases=["setrole"],
        description="set the role the bot will ping",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def set_role(
        self,
        ctx: commands.Context,
        role: Optional[disnake.Role] = None,
    ) -> None:
        "set the role the bot will ping"
        await ctx.send(**await valorant_helper.set_role(ctx, role))

    options: str = "options: add, show, delete"

    @commands.group(
        name="ping-image",
        aliases=["pingimage", "ping-img", "pingimg"],
        description="custom ping image functions",
        invoke_without_command=True,
    )
    async def ping_image(self, ctx: commands.Context) -> None:
        """custom image for the ping alert"""
        await ctx.send(
            content=f"custom image for the ping alert. {self.options}"
        )

    @ping_image.command(
        name="add", description="add custom image for the ping alert"
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def ping_image_add(
        self, ctx: commands.Context, new_image: Optional[str] = None
    ) -> None:
        """add custom image for the ping alert"""
        if new_image is None:
            await ctx.send(content=f'use {ctx.prefix}ping-image add "<url>"')
            return
        await ctx.send(**await valorant_helper.ping_image_add(ctx, new_image))

    @ping_image.command(
        name="show", description="show custom image for the ping alert"
    )
    async def ping_image_show(self, ctx: commands.Context) -> None:
        """show custom image for the ping alert"""
        await ctx.send(**await valorant_helper.ping_image_show(ctx))

    @ping_image.command(
        name="delete",
        aliases=["del", "remove"],
        description="delete custom image for the ping alert",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def ping_image_delete(self, ctx: commands.Context) -> None:
        """delete custom image for the ping alert"""
        await ctx.send(**await valorant_helper.ping_image_delete(ctx))

    @commands.group(
        name="feeder-message",
        aliases=["feedermessage", "feeder-msg", "feedermsg"],
        description="custom feeder messages functions",
        invoke_without_command=True,
    )
    async def feeder_message(self, ctx: commands.Context) -> None:
        """custom messages for the feeder alert"""
        await ctx.send(
            content=f"custom messages for the feeder alert. {self.options}"
        )

    @feeder_message.command(
        name="add", description="add custom messages for the feeder alert"
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_message_add(
        self, ctx: commands.Context, new_message: Optional[str] = None
    ) -> None:
        """add custom messages for the feeder alert"""
        if new_message is None:
            await ctx.send(
                content=f'use {ctx.prefix}feeder-message add "<message>"'
            )
            return
        await ctx.send(
            **await valorant_helper.feeder_message_add(ctx, new_message)
        )

    @feeder_message.command(
        name="show", description="show custom messages for the feeder alert"
    )
    async def feeder_message_show(self, ctx: commands.Context) -> None:
        """show custom messages for the feeder aler"""
        await ctx.send(**await valorant_helper.feeder_message_show(ctx))

    @feeder_message.command(
        name="delete",
        aliases=["del", "remove"],
        description="delete custom messages for the feeder alert",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_message_delete(self, ctx: commands.Context) -> None:
        """delete custom messages for the feeder alert"""
        await ctx.send(
            **await valorant_helper.feeder_message_delete(ctx)
        )

    @commands.group(
        name="feeder-image",
        aliases=["feederimage", "feeder-img", "feederimg"],
        description="custom feeder images functions",
        invoke_without_command=True,
    )
    async def feeder_image(self, ctx: commands.Context) -> None:
        """custom images for the feeder alert"""
        await ctx.send(
            content=f"custom images for the feeder alert. {self.options}"
        )

    @feeder_image.command(
        name="add", description="add custom images for the feeder alert"
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_image_add(
        self, ctx: commands.Context, new_image: Optional[str] = None
    ) -> None:
        """add custom images for the feeder alert"""
        if new_image is None:
            await ctx.send(content=f'use {ctx.prefix}feeder-image add "<url>"')
            return
        await ctx.send(
            **await valorant_helper.feeder_image_add(ctx, new_image)
        )

    @feeder_image.command(
        name="show", description="show custom images for the feeder alert"
    )
    async def feeder_image_show(self, ctx: commands.Context) -> None:
        """show custom images for the feeder alert"""
        await ctx.send(**await valorant_helper.feeder_image_show(ctx))

    @feeder_image.command(
        name="delete",
        aliases=["del", "remove"],
        description="delete custom images for the feeder alert",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_image_delete(self, ctx: commands.Context) -> None:
        """delete custom images for the feeder alert"""
        await ctx.send(
            **await valorant_helper.feeder_image_delete(ctx)
        )

    @commands.group(
        name="streaker-message",
        aliases=["streakermessage", "streaker-msg", "streakermsg"],
        description="custom streaker messages functions",
        invoke_without_command=True,
    )
    async def streaker_message(self, ctx: commands.Context) -> None:
        """custom messages for the streaker alert"""
        await ctx.send(
            content=f"custom messages for the streaker alert. {self.options}"
        )

    @streaker_message.command(
        name="add", description="add custom messages for the streaker alert"
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def streaker_message_add(
        self, ctx: commands.Context, new_message: Optional[str] = None
    ) -> None:
        """add custom messages for the streaker alert"""
        if new_message is None:
            await ctx.send(
                content=f'use {ctx.prefix}streaker-message add "<message>"'
            )
            return
        await ctx.send(
            **await valorant_helper.streaker_message_add(ctx, new_message)
        )

    @streaker_message.command(
        name="show", description="show custom messages for the streaker alert"
    )
    async def streaker_message_show(self, ctx: commands.Context) -> None:
        """show custom messages for the streaker alert"""
        await ctx.send(**await valorant_helper.streaker_message_show(ctx))

    @streaker_message.command(
        name="delete",
        aliases=["del", "remove"],
        description="delete custom messages for the streaker alert",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def streaker_message_delete(self, ctx: commands.Context) -> None:
        """delete custom messages for the streaker alert"""
        await ctx.send(**await valorant_helper.streaker_message_delete(ctx))


def setup(bot: commands.Bot) -> None:
    """loads game cog into bot"""
    bot.add_cog(Valorant())
    bot.add_cog(ValorantAdmin())
