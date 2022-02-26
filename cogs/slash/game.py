import disnake
from disnake.ext import tasks, commands

import os
import json
import aiohttp
import asyncio
import time
import sys

from helpers import json_helper

# RIOT_TOKEN = os.environ["RIOT_TOKEN"] not used at the moment

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found!")
else:
    with open("config.json") as file:
        config = json.load(file)

class Game(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.waitlist = {}
        self.valorant_watch_cycle.start()

    @commands.slash_command(name='jewels',
                            description='ping jewels role',
                            guild_ids=config['guilds'])
    async def jewelsPing(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        """pings @jewels role and sends image"""
        await inter.edit_original_message(content="<@&943511061447987281>", file=disnake.File('jewelsignal.jpg'))

    @commands.slash_command(name='valorant-info',
                            description='view valorant data in database',
                            guild_ids=config['guilds'])
    async def valorant_info(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        """returns user's valorant info from the database"""
        playerData = json_helper.load()
        user_id = str(inter.user.id)
        if user_id in playerData:
            user_data = playerData[user_id]
            embed = disnake.Embed(
                title="valorant info",
                description=f"<@{user_id}> saved info"
            )
            embed.set_thumbnail(
                url=inter.user.display_avatar.url
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
            await inter.edit_original_message(embed=embed)
        else:
            await inter.edit_original_message(content=f"<@{user_id}> not in database! do /valorant-watch first")

    @commands.slash_command(name='valorant-watch',
                            description='adds user into database',
                            guild_ids=config['guilds'])
    async def valorant_watch(self, inter: disnake.ApplicationCommandInteraction, name: str, tag: str):
        await inter.response.defer()
        """add user's valorant info to the database"""
        playerData = json_helper.load()
        user_id = str(inter.user.id)
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
                    await inter.edit_original_message(content=f"<@{user_id}> database updated, user added. remove using /valorant-unwatch")
                    json_helper.save(playerData)
                else:
                    await inter.edit_original_message(content=f"<@{user_id}> error connecting, database not updated. please try again")

    @commands.slash_command(name='valorant-unwatch',
                            description="removes user's valorant info from the database",
                            guild_ids=config['guilds'])
    async def valorant_unwatch(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        """removes user's valorant info from the database"""
        playerData = json_helper.load()
        user_id = str(inter.user.id)
        if user_id in playerData:
            del playerData[user_id]
            json_helper.save(playerData)
            await inter.edit_original_message(content=f"<@{user_id}> database updated, user removed. add again using /valorant-watch")
        else:
            await inter.edit_original_message(content=f"<@{user_id}> error updating, user not in database")

    @commands.slash_command(name='valorant-wait',
                            description='pings you when tagged user is done',
                            guild_ids=config['guilds'])
    async def valorant_wait(self, inter: disnake.ApplicationCommandInteraction, wait_user: disnake.User):
        await inter.response.defer()
        """pings you when tagged user is done"""
        playerData = json_helper.load()
        wait_user_id = str(wait_user.id)
        inter_user_id = str(inter.user.id)
        extra_message = ''
        if wait_user_id == inter_user_id:
            extra_message = 'interesting but ok. '
        if wait_user_id in playerData:
            if wait_user_id in self.waitlist:
                if inter_user_id in self.waitlist[wait_user_id]:
                    await inter.edit_original_message(content=f"{extra_message}<@{inter_user_id}> you are already waiting for <@{wait_user_id}>")
                    return
                else:
                    self.waitlist[wait_user_id] += [inter_user_id]
            else:
                self.waitlist[wait_user_id] = [inter_user_id]
            await inter.edit_original_message(content=f"{extra_message}<@{inter_user_id}> success, will notify when <@{wait_user_id}> is done")
        else:
            await inter.edit_original_message(content=f"{extra_message}<@{wait_user_id}> is not in database, unable to execute")
    
    @commands.slash_command(name='valorant-waitlist',
                            description='prints valorant waitlist',
                            guild_ids=config['guilds'])
    async def valorant_waitlist(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        """prints valorant waitlist"""
        embed = disnake.Embed(
            title="valorant waitlist",
            description="waitlist of watched users"
        )
        for user_id in self.waitlist:
            embed.add_field(
                name="user",
                value=f"<@{user_id}>",
                inline=False
            )
            embed.add_field(
                name="waiters",
                value=f"<@{'> <@'.join(self.waitlist[user_id])}>"
            )
        await inter.edit_original_message(embed=embed)

    @tasks.loop(seconds=30)
    async def valorant_watch_cycle(self):
        await self.bot.wait_until_ready()  # wait until the bot logs in
        channel = self.bot.get_channel(config['watch_channel']) # retrieves channel ID from config.json
        playerData = json_helper.load()
        for user_id in playerData:
            playerData = json_helper.load() # reloads playerData 
            user_data = playerData[user_id]
            if time.time() - user_data['lastTime'] > config["watch_cooldown"] * 60: # cooldown in seconds
                puuid = user_data['puuid']
                region = user_data['region']
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'https://api.henrikdev.xyz/valorant/v3/by-puuid/matches/{region}/{puuid}') as request:
                        # using this until access for riot granted async with session.get(f'https://{region}.api.riotgames.com/val/match/v1/matchlists/by-puuid/{puuid}?api_key={RIOT_TOKEN}') as request:
                        if request.status == 200:
                            data = await request.json()
                            if len(data['data']):
                                latestGame = data['data'][0]
                                startTime = latestGame['metadata']['game_start'] # given in s
                                duration = latestGame['metadata']['game_length'] / 1000 # given in ms 
                                recentTime = startTime + duration + 100
                                if user_data['lastTime'] < recentTime: # if latest game played is more recent than stored latest
                                    party = [new_user_id for player in latestGame['players']['all_players'] for new_user_id in playerData if player['puuid'] == playerData[new_user_id]['puuid']]
                                    # detects if multiple watched users are in the same game
                                    embed = disnake.Embed(
                                        title="valorant watch",
                                        description=f"<@{'> and <@'.join(party)}> just finished a game at <t:{int(recentTime)}>!"
                                    )
                                    await channel.send(embed=embed) # sends the notification embed

                                    combined_waiters = [] # init list of users to ping for waitlist
                                    for member_id in party:
                                        # sets party members to update last updated time if more recent
                                        if playerData[member_id]['lastTime'] < recentTime: playerData[member_id]['lastTime'] = recentTime
                                        if member_id in self.waitlist:
                                            combined_waiters += self.waitlist.pop(member_id)
                                    if combined_waiters: await channel.send(f"<@{'> <@'.join(combined_waiters)}> removing from waitlist") # pings waiters
                                    json_helper.save(playerData)
            await asyncio.sleep(0.5) # sleeps for number of seconds (avoid rate limit)
                          

def setup(bot: commands.Bot):
    bot.add_cog(Game(bot))
