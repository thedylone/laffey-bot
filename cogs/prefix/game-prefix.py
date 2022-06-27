import disnake
from disnake.ext import commands

from helpers import valorant_helper


class Valorant(commands.Cog, name="valorant"):
    """valorant related commands"""

    COG_EMOJI = "🕹️"

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="valorant-ping",
        aliases=["valorantping", "valping", "vping", "jewels"],
        description="pings role",
    )
    @commands.guild_only()
    async def valorant_ping(self, ctx: commands.Context):
        """pings role and sends optional image"""
        content, embed, file = await valorant_helper.ping(self.bot, ctx)
        await ctx.send(content=content, embed=embed, file=file)

    @commands.command(
        name="valorant-info",
        aliases=["valorantinfo", "valinfo", "vinfo"],
        description="view valorant data in database",
    )
    async def valorant_info(self, ctx: commands.Context, user: disnake.User = None):
        """returns user's valorant info from the database"""
        content, embed = await valorant_helper.info(self.bot, ctx, user)
        await ctx.send(content=content, embed=embed)

    @commands.command(
        name="valorant-watch",
        aliases=["valorantwatch", "valwatch", "vwatch"],
        description="adds user into database",
    )
    async def valorant_watch(
        self, ctx: commands.Context, name: str = None, tag: str = None
    ):
        """add user's valorant info to the database.
        e.g. ?vwatch GuessJewels#peko"""
        if tag == None:
            if not name or "#" not in name:
                content = f"use {ctx.prefix}valorant-watch <name> <tag>"
                await ctx.send(content=content)
                return
            else:
                name, tag = name.split('#')[:2]
        message = await ctx.send(content="retrieving data...")
        content = await valorant_helper.watch(self.bot, ctx, name, tag)
        await message.edit(content=content)

    @commands.command(
        name="valorant-unwatch",
        aliases=["valorantunwatch", "valunwatch", "vunwatch"],
        description="removes user's valorant info from the database",
    )
    async def valorant_unwatch(self, ctx: commands.Context):
        """removes user's valorant info from the database"""
        content = await valorant_helper.unwatch(self.bot, ctx)
        await ctx.send(content=content)

    @commands.command(
        name="valorant-wait",
        aliases=["valorantwait", "valwait", "vwait"],
        description="pings you when tagged user is done",
    )
    async def valorant_wait(self, ctx: commands.Context, *wait_users: disnake.User):
        """pings you when tagged user is done"""
        content = await valorant_helper.wait(self.bot, ctx, *wait_users)
        await ctx.send(content=content)

    @commands.command(
        name="valorant-waitlist",
        aliases=["valorantwaitlist", "valwaitlist", "vwaitlist"],
        description="prints valorant waitlist",
    )
    async def valorant_waitlist(self, ctx: commands.Context):
        """prints valorant waitlist"""
        embed = await valorant_helper.waitlist(self.bot, ctx)
        await ctx.send(embed=embed)


class ValorantAdmin(commands.Cog, name="valorant admin"):
    """valorant admin commands"""

    COG_EMOJI = "🎮"

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="set-channel",
        aliases=["setchannel"],
        description="set the channel the bot will send updates to",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def set_channel(
        self, ctx: commands.Context, channel: disnake.TextChannel = None
    ):
        """set the channel the bot will send updates to"""
        content = await valorant_helper.set_channel(self.bot, ctx, channel)
        await ctx.send(content=content)

    @commands.command(
        name="set-role",
        aliases=["setrole"],
        description="set the role the bot will ping",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def set_role(self, ctx: commands.Context, role: disnake.Role = None):
        "set the role the bot will ping"
        content = await valorant_helper.set_role(self.bot, ctx, role)
        await ctx.send(content=content)

    @commands.group(
        name="ping-image",
        aliases=["pingimage", "ping-img", "pingimg"],
        description="custom ping image functions",
        invoke_without_command=True,
    )
    async def ping_image(self, ctx: commands.Context):
        """custom image for the ping alert"""
        await ctx.send(
            content="custom image for the ping alert. options: add, show, delete"
        )

    @ping_image.command(name="add", description="add custom image for the ping alert")
    @commands.has_guild_permissions(manage_messages=True)
    async def ping_image_add(self, ctx: commands.Context, new_image: str = None):
        """add custom image for the ping alert"""
        if new_image:
            content = await valorant_helper.ping_image_add(self.bot, ctx, new_image)
            await ctx.send(content=content)
        else:
            await ctx.send(
                content=f'use {ctx.prefix}ping-image add "<new image url>" (include the "") '
            )

    @ping_image.command(name="show", description="show custom image for the ping alert")
    async def ping_image_show(self, ctx: commands.Context):
        """show custom image for the ping alert"""
        content, embed = await valorant_helper.ping_image_show(self.bot, ctx)
        await ctx.send(content=content, embed=embed)

    @ping_image.command(
        name="delete",
        aliases=["del", "remove"],
        description="delete custom image for the ping alert",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def ping_image_delete(self, ctx: commands.Context):
        """delete custom image for the ping alert"""
        content = await valorant_helper.ping_image_delete(self.bot, ctx)
        await ctx.send(content=content)

    @commands.group(
        name="feeder-message",
        aliases=["feedermessage", "feeder-msg", "feedermsg"],
        description="custom feeder messages functions",
        invoke_without_command=True,
    )
    async def feeder_message(self, ctx: commands.Context):
        """custom messages for the feeder alert"""
        await ctx.send(
            content="custom messages for the feeder alert. options: add, show, delete"
        )

    @feeder_message.command(
        name="add", description="add custom messages for the feeder alert"
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_message_add(self, ctx: commands.Context, new_message: str = None):
        """add custom messages for the feeder alert"""
        if new_message:
            out = await valorant_helper.feeder_message_add(self.bot, ctx, new_message)
            await ctx.send(out)
        else:
            await ctx.send(
                content=f'use {ctx.prefix}feeder-message add "<new message>" (include the "") '
            )

    @feeder_message.command(
        name="show", description="show custom messages for the feeder alert"
    )
    async def feeder_message_show(self, ctx: commands.Context):
        """show custom messages for the feeder aler"""
        content, embed, view = await valorant_helper.feeder_message_show(self.bot, ctx)
        await ctx.send(content=content, embed=embed, view=view)

    @feeder_message.command(
        name="delete",
        aliases=["del", "remove"],
        description="delete custom messages for the feeder alert",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_message_delete(self, ctx: commands.Context):
        """delete custom messages for the feeder alert"""
        content, view = await valorant_helper.feeder_message_delete(self.bot, ctx)
        await ctx.send(content=content, view=view)

    @commands.group(
        name="feeder-image",
        aliases=["feederimage", "feeder-img", "feederimg"],
        description="custom feeder images functions",
        invoke_without_command=True,
    )
    async def feeder_image(self, ctx: commands.Context):
        """custom images for the feeder alert"""
        await ctx.send(
            content="custom images for the feeder alert. options: add, show, delete"
        )

    @feeder_image.command(
        name="add", description="add custom images for the feeder alert"
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_image_add(self, ctx: commands.Context, new_image: str = None):
        """add custom images for the feeder alert"""
        if new_image:
            out = await valorant_helper.feeder_image_add(self.bot, ctx, new_image)
            await ctx.send(out)
        else:
            await ctx.send(
                content=f'use {ctx.prefix}feeder-image add "<new image url>" (include the "") '
            )

    @feeder_image.command(
        name="show", description="show custom images for the feeder alert"
    )
    async def feeder_image_show(self, ctx: commands.Context):
        """show custom images for the feeder alert"""
        content, embed, view = await valorant_helper.feeder_image_show(self.bot, ctx)
        await ctx.send(content=content, embed=embed, view=view)

    @feeder_image.command(
        name="delete",
        aliases=["del", "remove"],
        description="delete custom images for the feeder alert",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_image_delete(self, ctx: commands.Context):
        """delete custom images for the feeder alert"""
        content, view = await valorant_helper.feeder_image_delete(self.bot, ctx)
        await ctx.send(content=content, view=view)

    @commands.group(
        name="streaker-message",
        aliases=["streakermessage", "streaker-msg", "streakermsg"],
        description="custom streaker messages functions",
        invoke_without_command=True,
    )
    async def streaker_message(self, ctx: commands.Context):
        """custom messages for the streaker alert"""
        await ctx.send(
            content="custom messages for the streaker alert. options: add, show, delete"
        )

    @streaker_message.command(
        name="add", description="add custom messages for the streaker alert"
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def streaker_message_add(
        self, ctx: commands.Context, new_message: str = None
    ):
        """add custom messages for the streaker alert"""
        if new_message:
            out = await valorant_helper.streaker_message_add(self.bot, ctx, new_message)
            await ctx.send(out)
        else:
            await ctx.send(
                content=f'use {ctx.prefix}streaker-message add "<new message>" (include the "") '
            )

    @streaker_message.command(
        name="show", description="show custom messages for the streaker alert"
    )
    async def streaker_message_show(self, ctx: commands.Context):
        """show custom messages for the streaker alert"""
        content, embed, view = await valorant_helper.streaker_message_show(
            self.bot, ctx
        )
        await ctx.send(content=content, embed=embed, view=view)

    @streaker_message.command(
        name="delete",
        aliases=["del", "remove"],
        description="delete custom messages for the streaker alert",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def streaker_message_delete(self, ctx: commands.Context):
        """delete custom messages for the streaker alert"""
        content, view = await valorant_helper.streaker_message_delete(self.bot, ctx)
        await ctx.send(content=content, view=view)


def setup(bot: commands.Bot):
    bot.add_cog(Valorant(bot))
    bot.add_cog(ValorantAdmin(bot))
