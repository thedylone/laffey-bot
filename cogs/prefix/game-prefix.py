import disnake
from disnake.ext import commands

import os
import json
import aiohttp
import time
import sys

from helpers import json_helper

# RIOT_TOKEN = os.environ["RIOT_TOKEN"] not used at the moment

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found!")
else:
    with open("config.json", encoding="utf-8") as file:
        config = json.load(file)


class Game(commands.Cog, name="game"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="jewels", description="pings role")
    async def jewels_ping(self, ctx: commands.Context):
        """pings @jewels role and sends image"""
        await ctx.send(
            f"<@&{config['ping_role']}>", file=disnake.File("jewelsignal.jpg")
        )

    @commands.command(
        name="valorant-info",
        aliases=["valorantinfo", "valinfo", "vinfo"],
        description="view valorant data in database",
    )
    async def valorant_info(self, ctx: commands.Context, user: disnake.User = None):
        """returns user's valorant info from the database"""
        player_data = json_helper.load()
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
                content=f"<@{user_id}> not in database! do /valorant-watch first"
            )

    @commands.command(
        name="valorant-watch",
        aliases=["valorantwatch", "valwatch", "vwatch"],
        description="adds user into database",
    )
    async def valorant_watch(self, ctx: commands.Context, name: str, tag: str):
        """add user's valorant info to the database"""
        player_data = json_helper.load()
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
                    }
                    await ctx.send(
                        content=f"<@{user_id}> database updated, user added. remove using /valorant-unwatch"
                    )
                    json_helper.save(player_data)
                else:
                    await ctx.send(
                        content=f"<@{user_id}> error connecting, database not updated. please try again"
                    )

    @valorant_watch.error
    async def valorant_watch_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.MissingRequiredArgument):
            message = f"use {config['prefix']}valorant-watch <name> <tag without #>"
        await ctx.send(message)

    @commands.command(
        name="valorant-unwatch",
        aliases=["valorantunwatch", "valunwatch", "vunwatch"],
        description="removes user's valorant info from the database",
    )
    async def valorant_unwatch(self, ctx: commands.Context):
        """removes user's valorant info from the database"""
        player_data = json_helper.load()
        user_id = str(ctx.author.id)
        if user_id in player_data:
            del player_data[user_id]
            json_helper.save(player_data)
            await ctx.send(
                content=f"<@{user_id}> database updated, user removed. add again using /valorant-watch"
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
            await ctx.send(content=f"<@{ctx_user_id}> use {config['prefix']}valorant-wait <tag the user you are waiting for>")
            return
        player_data = json_helper.load()
        extra_message = ""
        success_waiting = []
        already_waiting = []
        not_in_database = []
        for wait_user in wait_users:
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
        success_message = f"success, will notify when <@{'> <@'.join(success_waiting)}> {'is' if len(success_waiting) == 1 else 'are'} done. " if success_waiting else ""
        already_message = f"you are already waiting for <@{'> <@'.join(already_waiting)}>. " if already_waiting else ""
        not_in_database_message = f"<@{'> <@'.join(not_in_database)}> not in database, unable to wait." if not_in_database else ""
        await ctx.send(content=f"{extra_message}<@{ctx_user_id}> {success_message}{already_message}{not_in_database_message}")


    @commands.command(
        name="valorant-waitlist",
        aliases=["valorantwaitlist", "valwaitlist", "vwaitlist"],
        description="prints valorant waitlist",
    )
    async def valorant_waitlist(self, ctx: commands.Context):
        """prints valorant waitlist"""
        embed = disnake.Embed(
            title="valorant waitlist", description="waitlist of watched users"
        )
        embed.set_thumbnail(
            url="https://cdn.vox-cdn.com/uploads/chorus_image/image/66615355/VALORANT_Jett_Red_crop.0.jpg"
        )
        for user_id in self.bot.valorant_waitlist:
            embed.add_field(name="user", value=f"<@{user_id}>", inline=False)
            embed.add_field(
                name="waiters",
                value=f"<@{'> <@'.join(self.bot.valorant_waitlist[user_id])}>",
            )
        await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Game(bot))
