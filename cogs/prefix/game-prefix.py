import disnake
from disnake.ext import commands

import aiohttp
import time

from helpers import json_helper, valorant_helper

# RIOT_TOKEN = os.environ["RIOT_TOKEN"] not used at the moment


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
        content, file = await valorant_helper.ping(ctx)
        await ctx.send(content=content, file=file)

    @commands.command(
        name="valorant-info",
        aliases=["valorantinfo", "valinfo", "vinfo"],
        description="view valorant data in database",
    )
    async def valorant_info(self, ctx: commands.Context, user: disnake.User = None):
        """returns user's valorant info from the database"""
        content, embed = await valorant_helper.info(ctx, user)
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
            content = await valorant_helper.watch(ctx, name, tag)
        await ctx.send(content=content)

    @commands.command(
        name="valorant-unwatch",
        aliases=["valorantunwatch", "valunwatch", "vunwatch"],
        description="removes user's valorant info from the database",
    )
    async def valorant_unwatch(self, ctx: commands.Context):
        """removes user's valorant info from the database"""
        content = await valorant_helper.unwatch(ctx)
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
        if channel == None:
            channel = ctx.channel
        guild = ctx.guild
        guild_data = json_helper.load("guildData.json")
        guild_data[str(guild.id)]["watch_channel"] = channel.id
        json_helper.save(guild_data, "guildData.json")
        await ctx.send(f"successfully set `#{channel}` as watch channel for `{guild}`")

    @commands.command(
        name="set-role",
        aliases=["setrole"],
        description="set the role the bot will ping",
    )
    @commands.has_guild_permissions(manage_messages=True)
    async def set_role(self, ctx: commands.Context, role: disnake.Role = None):
        "set the role the bot will ping"
        if role == None:
            await ctx.send(content=f"use {ctx.prefix}set-role <tag the role>")
            return
        guild = ctx.guild
        guild_data = json_helper.load("guildData.json")
        guild_data[str(guild.id)]["ping_role"] = role.id
        json_helper.save(guild_data, "guildData.json")
        await ctx.send(f"successfully set role `{role}` as watch channel for `{guild}`")

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
                out = await valorant_helper.feeder_message_add(ctx, new_message)
                await ctx.send(out)
            else:
                await ctx.send(
                    content=f'use {ctx.prefix}feeder-message add "<new message>" (include the "") '
                )
        elif option == "show":
            content, embed, view = await valorant_helper.feeder_message_show(ctx)
            await ctx.send(content=content, embed=embed, view=view)
        elif option == "delete" or option == "del":
            content, view = await valorant_helper.feeder_message_delete(ctx)
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
                out = await valorant_helper.feeder_image_add(ctx, new_image)
                await ctx.send(out)
            else:
                await ctx.send(
                    content=f'use {ctx.prefix}feeder-image add "<new image url>" (include the "") '
                )
        elif option == "show":
            content, embed, view = await valorant_helper.feeder_image_show(ctx)
            await ctx.send(content=content, embed=embed, view=view)
        elif option == "delete" or option == "del":
            content, view = await valorant_helper.feeder_image_delete(ctx)
            await ctx.send(content=content, view=view)
        else:
            await ctx.send(
                content=f"use {ctx.prefix}feeder-image <add | show | delete>"
            )


def setup(bot: commands.Bot):
    bot.add_cog(Valorant(bot))
    bot.add_cog(ValorantAdmin(bot))
