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
        player_data = json_helper.load("playerData.json")
        if user == None:
            user = ctx.author
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
            await ctx.send(embed=embed)
        else:
            await ctx.send(
                content=f"<@{user_id}> not in database! do {ctx.prefix}valorant-watch first"
            )

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
            await ctx.send(
                content=f"use {ctx.prefix}valorant-watch <name> <tag without #>"
            )
            return
        if isinstance(ctx.channel, disnake.channel.DMChannel):
            guild_id = 0
        else:
            guild_data = json_helper.load("guildData.json")
            guild_id = ctx.guild.id
            if (
                str(guild_id) not in guild_data
                or "watch_channel" not in guild_data[str(guild_id)]
                or guild_data[str(guild_id)]["watch_channel"] == 0
            ):
                await ctx.send(
                    f"please set the watch channel for the guild first using {ctx.prefix}valorant-set-channel! you can also DM me and i will DM you for each update instead!"
                )
                return
        player_data = json_helper.load("playerData.json")
        user_id = str(ctx.author.id)
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.henrikdev.xyz/valorant/v1/account/{name}/{tag}"
            ) as request:
                # using this until access for riot api granted async with session.get(f'https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}?api_key={RIOT_TOKEN}') as request:
                if request.status == 200:
                    data = await request.json()
                    player_data[user_id] = {
                        "name": name,
                        "tag": tag,
                        "region": data["data"]["region"],
                        "puuid": data["data"]["puuid"],
                        "lastTime": time.time(),
                        "streak": 0,
                        "guild": guild_id,
                    }
                    await ctx.send(
                        content=f"<@{user_id}> database updated, user added. remove using {ctx.prefix}valorant-unwatch"
                    )
                    json_helper.save(player_data, "playerData.json")
                else:
                    await ctx.send(
                        content=f"<@{user_id}> error connecting, database not updated. please try again"
                    )

    @commands.command(
        name="valorant-unwatch",
        aliases=["valorantunwatch", "valunwatch", "vunwatch"],
        description="removes user's valorant info from the database",
    )
    async def valorant_unwatch(self, ctx: commands.Context):
        """removes user's valorant info from the database"""
        player_data = json_helper.load("playerData.json")
        user_id = str(ctx.author.id)
        if user_id in player_data:
            del player_data[user_id]
            json_helper.save(player_data, "playerData.json")
            await ctx.send(
                content=f"<@{user_id}> database updated, user removed. add again using {ctx.prefix}valorant-watch"
            )
        else:
            await ctx.send(content=f"<@{user_id}> error updating, user not in database")

    @commands.command(
        name="valorant-wait",
        aliases=["valorantwait", "valwait", "vwait"],
        description="pings you when tagged user is done",
    )
    async def valorant_wait(self, ctx: commands.Context, *wait_users: disnake.User):
        """pings you when tagged user is done"""
        ctx_user_id = str(ctx.author.id)
        if len(wait_users) == 0:
            await ctx.send(
                content=f"<@{ctx_user_id}> use {ctx.prefix}valorant-wait <tag the user you are waiting for>"
            )
            return
        player_data = json_helper.load("playerData.json")
        extra_message = ""
        success_waiting = []
        already_waiting = []
        not_in_database = []
        for wait_user in list(set(wait_users)):
            wait_user_id = str(wait_user.id)
            if wait_user_id == ctx_user_id:
                extra_message = "interesting but ok. "
            if wait_user_id in player_data:
                if wait_user_id in self.bot.valorant_waitlist:
                    if ctx_user_id in self.bot.valorant_waitlist[wait_user_id]:
                        already_waiting.append(wait_user_id)
                    else:
                        self.bot.valorant_waitlist[wait_user_id] += [ctx_user_id]
                        success_waiting.append(wait_user_id)
                else:
                    self.bot.valorant_waitlist[wait_user_id] = [ctx_user_id]
                    success_waiting.append(wait_user_id)
            else:
                not_in_database.append(wait_user_id)
        success_message = (
            f"success, will notify when <@{'> <@'.join(success_waiting)}> {'is' if len(success_waiting) == 1 else 'are'} done. "
            if success_waiting
            else ""
        )
        already_message = (
            f"you are already waiting for <@{'> <@'.join(already_waiting)}>. "
            if already_waiting
            else ""
        )
        not_in_database_message = (
            f"<@{'> <@'.join(not_in_database)}> not in database, unable to wait."
            if not_in_database
            else ""
        )
        await ctx.send(
            content=f"{extra_message}<@{ctx_user_id}> {success_message}{already_message}{not_in_database_message}"
        )

    @commands.command(
        name="valorant-waitlist",
        aliases=["valorantwaitlist", "valwaitlist", "vwaitlist"],
        description="prints valorant waitlist",
    )
    async def valorant_waitlist(self, ctx: commands.Context):
        """prints valorant waitlist"""
        if isinstance(ctx.channel, disnake.channel.DMChannel):
            guild_id = 0
        else:
            guild_id = ctx.guild.id
        player_data = json_helper.load("playerData.json")
        embed = disnake.Embed(
            title="valorant waitlist", description="waitlist of watched users"
        )
        embed.set_thumbnail(
            url="https://cdn.vox-cdn.com/uploads/chorus_image/image/66615355/VALORANT_Jett_Red_crop.0.jpg"
        )
        for user_id in self.bot.valorant_waitlist:
            print(user_id)
            print(ctx.author.id)
            if guild_id == 0 and ctx.author.id in self.bot.valorant_waitlist[user_id]:
                embed.add_field(name="user", value=f"<@{user_id}>", inline=False)
                embed.add_field(
                    name="waiters",
                    value=f"<@{ctx.author.id}>",
                )
            elif (
                user_id == str(ctx.author.id)
                or guild_id
                and player_data[user_id]["guild"] == guild_id
            ):
                embed.add_field(name="user", value=f"<@{user_id}>", inline=False)
                embed.add_field(
                    name="waiters",
                    value=f"<@{'> <@'.join(self.bot.valorant_waitlist[user_id])}>",
                )
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
