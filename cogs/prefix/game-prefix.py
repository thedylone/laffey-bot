import disnake
from disnake.ext import commands

from helpers import valorant_helper


class Valorant(commands.Cog, name="valorant"):
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
        content, file = await valorant_helper.ping(self.bot, ctx)
        await ctx.send(content=content, file=file)

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
        """add user's valorant info to the database"""
        if name == None or tag == None:
            content = f"use {ctx.prefix}valorant-watch <name> <tag without #>"
        else:
            content = await valorant_helper.watch(self.bot, ctx, name, tag)
        await ctx.send(content=content)

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

    @commands.command(
        name="feeder-message",
        aliases=["feedermessage", "feeder-msg", "feedermsg"],
        description="custom feeder messages functions",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_message(
        self, ctx: commands.Context, option: str = None, new_message: str = None
    ):
        """custom feeder messages functions"""
        if option == "add":
            if new_message:
                out = await valorant_helper.feeder_message_add(
                    self.bot, ctx, new_message
                )
                await ctx.send(out)
            else:
                await ctx.send(
                    content=f'use {ctx.prefix}feeder-message add "<new message>" (include the "") '
                )
        elif option == "show":
            content, embed, view = await valorant_helper.feeder_message_show(
                self.bot, ctx
            )
            await ctx.send(content=content, embed=embed, view=view)
        elif option == "delete" or option == "del":
            content, view = await valorant_helper.feeder_message_delete(self.bot, ctx)
            await ctx.send(content=content, view=view)
        else:
            await ctx.send(
                content=f"use {ctx.prefix}feeder-message <add | show | delete>"
            )

    @commands.command(
        name="feeder-image",
        aliases=["feederimage", "feeder-img", "feederimg"],
        description="custom feeder images functions",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def feeder_image(
        self, ctx: commands.Context, option: str = None, new_image: str = None
    ):
        """custom feeder images functions"""
        if option == "add":
            if new_image:
                out = await valorant_helper.feeder_image_add(self.bot, ctx, new_image)
                await ctx.send(out)
            else:
                await ctx.send(
                    content=f'use {ctx.prefix}feeder-image add "<new image url>" (include the "") '
                )
        elif option == "show":
            content, embed, view = await valorant_helper.feeder_image_show(
                self.bot, ctx
            )
            await ctx.send(content=content, embed=embed, view=view)
        elif option == "delete" or option == "del":
            content, view = await valorant_helper.feeder_image_delete(self.bot, ctx)
            await ctx.send(content=content, view=view)
        else:
            await ctx.send(
                content=f"use {ctx.prefix}feeder-image <add | show | delete>"
            )

    @commands.command(
        name="streaker-message",
        aliases=["streakermessage", "streaker-msg", "streakermsg"],
        description="custom streaker messages functions",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def streaker_message(
        self, ctx: commands.Context, option: str = None, new_message: str = None
    ):
        """custom streaker messages functions"""
        if option == "add":
            if new_message:
                out = await valorant_helper.streaker_message_add(
                    self.bot, ctx, new_message
                )
                await ctx.send(out)
            else:
                await ctx.send(
                    content=f'use {ctx.prefix}streaker-message add "<new message>" (include the "") '
                )
        elif option == "show":
            content, embed, view = await valorant_helper.streaker_message_show(
                self.bot, ctx
            )
            await ctx.send(content=content, embed=embed, view=view)
        elif option == "delete" or option == "del":
            content, view = await valorant_helper.streaker_message_delete(self.bot, ctx)
            await ctx.send(content=content, view=view)
        else:
            await ctx.send(
                content=f"use {ctx.prefix}streaker-message <add | show | delete>"
            )


def setup(bot: commands.Bot):
    bot.add_cog(Valorant(bot))
    bot.add_cog(ValorantAdmin(bot))
