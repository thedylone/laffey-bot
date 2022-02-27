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
    with open("config.json") as file:
        config = json.load(file)

class Game(commands.Cog, name='game'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='jewels',
                      description='pings role')
    async def jewelsPing(self, ctx: commands.Context):
        """pings @jewels role and sends image"""
        await ctx.send(f"<@&{config['ping_role']}>",
                       file=disnake.File('jewelsignal.jpg'))

    @commands.command(name='valorant-info',
                      description='view valorant data in database')
    async def valorant_info(self, ctx: commands.Context):
        """returns user's valorant info from the database"""
        playerData = json_helper.load()
        user_id = str(ctx.author.id)
        if user_id in playerData:
            user_data = playerData[user_id]
            embed = disnake.Embed(
                title="valorant info",
                description=f"<@{user_id}> saved info"
            )
            embed.set_thumbnail(
                url=ctx.author.display_avatar.url
            )
            embed.add_field(
                name="username",
                value=f"{user_data['name']}",
                inline= True
            )
            embed.add_field(
                name="tag",
                value=f"#{user_data['tag']}",
                inline= True
            )
            embed.add_field(
                name="last updated",
                value=f"<t:{int(user_data['lastTime'])}>"
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(content=f"<@{user_id}> not in database! do /valorant-watch first")

    @commands.command(name='valorant-watch',
                        description='adds user into database')
    async def valorant_watch(self, ctx: commands.Context, name: str, tag: str):
        """add user's valorant info to the database"""
        playerData = json_helper.load()
        user_id = str(ctx.author.id)
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.henrikdev.xyz/valorant/v1/account/{name}/{tag}') as request:
            # using this until access for riot api granted async with session.get(f'https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}?api_key={RIOT_TOKEN}') as request:
                if request.status == 200:
                    data = await request.json()
                    playerData[user_id] = {
                        'name': name,
                        'tag': tag,
                        'region': data['data']['region'],
                        'puuid': data['data']['puuid'],
                        'lastTime': time.time()
                    }
                    await ctx.send(content=f"<@{user_id}> database updated, user added. remove using /valorant-unwatch")
                    json_helper.save(playerData)
                else:
                    await ctx.send(content=f"<@{user_id}> error connecting, database not updated. please try again")
    
    @valorant_watch.error
    async def valorant_watch_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            message = f"use {config['prefix']}valorant-watch <name> <tag without #>"
        await ctx.send(message)

    @commands.command(name='valorant-unwatch',
                      description="removes user's valorant info from the database")
    async def valorant_unwatch(self, ctx: commands.Context):
        """removes user's valorant info from the database"""
        playerData = json_helper.load()
        user_id = str(ctx.author.id)
        if user_id in playerData:
            del playerData[user_id]
            json_helper.save(playerData)
            await ctx.send(content=f"<@{user_id}> database updated, user removed. add again using /valorant-watch")
        else:
            await ctx.send(content=f"<@{user_id}> error updating, user not in database")
    
    @commands.command(name='valorant-wait',
                      description="pings you when tagged user is done")
    async def valorant_wait(self, ctx: commands.Context, wait_user: disnake.User):
        """pings you when tagged user is done"""
        playerData = json_helper.load()
        wait_user_id = str(wait_user.id)
        inter_user_id = str(ctx.author.id)
        extra_message = ''
        if wait_user_id == inter_user_id:
            extra_message = 'interesting but ok. '
        if wait_user_id in playerData:
            if wait_user_id in self.bot.valorant_waitlist:
                if inter_user_id in self.bot.valorant_waitlist[wait_user_id]:
                    await ctx.send(content=f"{extra_message}<@{inter_user_id}> you are already waiting for <@{wait_user_id}>")
                    return
                else:
                    self.bot.valorant_waitlist[wait_user_id] += [inter_user_id]
            else:
                self.bot.valorant_waitlist[wait_user_id] = [inter_user_id]
            await ctx.send(content=f"{extra_message}<@{inter_user_id}> success, will notify when <@{wait_user_id}> is done")
        else:
            await ctx.send(content=f"{extra_message}<@{wait_user_id}> is not in database, unable to execute")

    @valorant_wait.error
    async def valorant_wait_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingRequiredArgument):
            message = f"use {config['prefix']}valorant-wait <tag the user you are waiting for>"
        await ctx.send(message)

    @commands.command(name='valorant-waitlist',
                            description='prints valorant waitlist',
                            guild_ids=config['guilds'])
    async def valorant_waitlist(self, ctx: commands.Context):
        """prints valorant waitlist"""
        embed = disnake.Embed(
            title="valorant waitlist",
            description="waitlist of watched users"
        )
        embed.set_thumbnail(
            url="https://cdn.vox-cdn.com/uploads/chorus_image/image/66615355/VALORANT_Jett_Red_crop.0.jpg"
        )
        for user_id in self.bot.valorant_waitlist:
            embed.add_field(
                name="user",
                value=f"<@{user_id}>",
                inline=False
            )
            embed.add_field(
                name="waiters",
                value=f"<@{'> <@'.join(self.bot.valorant_waitlist[user_id])}>"
            )
        await ctx.send(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(Game(bot))
