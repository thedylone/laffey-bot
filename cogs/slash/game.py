import disnake
from disnake.ext import tasks, commands

import os
import json
import aiohttp
import asyncio
import time
import sys

RIOT_TOKEN = os.environ["RIOT_TOKEN"]

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found!")
else:
    with open("config.json") as file:
        config = json.load(file)


def loadData() -> None:
    if not os.path.isfile("playerData.json"):
        print("'playerData.json' not found, using empty data...")
        return {}
    else:
        with open("playerData.json") as file:
            return json.load(file)

def saveData(data) -> None:
    with open("playerData.json", "w") as file:
        file.seek(0)
        json.dump(data, file, indent=4)

class Game(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.valorantcycle.start()

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
    async def valorantinfo(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        """returns user's valorant info from the database"""
        playerData = loadData()
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
    async def valorantwatch(self, inter: disnake.ApplicationCommandInteraction, name: str, tag: str):
        await inter.response.defer()
        """add user's valorant info to the database"""
        playerData = loadData()
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
                    saveData(playerData)
                else:
                    await inter.edit_original_message(content=f"<@{user_id}> error connecting, database not updated. please try again")

    @commands.slash_command(name='valorant-unwatch',
                            description='removes user from database',
                            guild_ids=config['guilds'])
    async def valorantunwatch(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        """removes user's valorant info from the database"""
        playerData = loadData()
        user_id = str(inter.user.id)
        if user_id in playerData:
            del playerData[user_id]
            saveData(playerData)
            await inter.edit_original_message(content=f"<@{user_id}> database updated, user removed. add again using /valorant-watch")
        else:
            await inter.edit_original_message(content=f"<@{user_id}> error updating, user not in database")

    @tasks.loop(seconds=30)
    async def valorantcycle(self):
        await self.bot.wait_until_ready()  # wait until the bot logs in
        channel = self.bot.get_channel(config['watch_channel']) # retrieves channel ID from config.json
        playerData = loadData()
        for user_id in playerData:
            playerData = loadData()
            user_data = playerData[user_id]
            if time.time() - user_data['lastTime'] > config["watch_cooldown"] * 60: # cooldown in seconds
                puuid = user_data['puuid']
                region = user_data['region']
                name = user_data['name']
                tag = user_data['tag']
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'https://api.henrikdev.xyz/valorant/v3/matches/{region}/{name}/{tag}') as request:
                        # using this until access for riot granted async with session.get(f'https://{region}.api.riotgames.com/val/match/v1/matchlists/by-puuid/{puuid}?api_key={RIOT_TOKEN}') as request:
                        if request.status == 200:
                            data = await request.json()
                            if len(data['data']):
                                latestGame = data['data'][0]
                                recentTime = latestGame['metadata']['game_start']
                                if user_data['lastTime'] < recentTime: # if latest game played is more recent than stored latest
                                    party = [new_user_id for player in latestGame['players']['all_players'] for new_user_id in playerData if player['puuid'] == playerData[new_user_id]['puuid']]
                                    # detects if multiple watched users are in the same game
                                    embed = disnake.Embed(
                                        title="valorant watch",
                                        description=f"<@{'> and <@'.join(party)}> just finished a game!"
                                    )
                                    await channel.send(embed=embed)
                                    for member_id in party:
                                        # sets party members to update last updated time
                                        playerData[member_id]['lastTime'] = recentTime
                                    saveData(playerData)
            await asyncio.sleep(0.5) # sleeps for number of seconds (avoid rate limit)
                          

def setup(bot: commands.Bot):
    bot.add_cog(Game(bot))
