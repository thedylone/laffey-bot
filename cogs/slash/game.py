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
                            description='ping jewels role')
    async def jewelsPing(self, inter: disnake.ApplicationCommandInteraction):
        """pings @jewels role and sends image"""
        await inter.response.send_message("<@&943511061447987281>", file=disnake.File('jewelsignal.jpg'))

    @commands.slash_command(name='valorant-info',
                            description='view valorant data in database')
    async def valorantinfo(self, inter: disnake.ApplicationCommandInteraction):
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
                value=f"<t:{user_data['lastTime']}>"
            )
            await inter.response.send_message(embed=embed)
        else:
            await inter.response.send_message(f"<@{user_id}> not in database! do /valorant-watch first")

    @commands.slash_command(name='valorant-watch',
                            description='adds user into database')
    async def valorantwatch(self, inter: disnake.ApplicationCommandInteraction, name: str, tag: str, region: str='asia'):
        playerData = loadData()
        user_id = str(inter.user.id)
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}?api_key={RIOT_TOKEN}') as request:
                if request.status == 200:
                    data = await request.json()
                    playerData[user_id] = {
                        'name': name,
                        'tag': tag,
                        'region': region,
                        'puuid': data['puuid'],
                        'lastTime': time.time()
                    }
                    await inter.response.send_message("database updated, user added. remove using /valorant-unwatch")
                    saveData(playerData)
                else:
                    await inter.response.send_message("error connecting, database not updated")

    @commands.slash_command(name='valorant-unwatch',
                            description='removes user from database')
    async def valorantunwatch(self, inter: disnake.ApplicationCommandInteraction):
        playerData = loadData()
        user_id = str(inter.user.id)
        if user_id in playerData:
            del playerData[user_id]
            saveData(playerData)
            await inter.response.send_message("database updated, user removed. add again using /valorant-watch")
        else:
            await inter.response.send_message("error updating, user not in database")

    @tasks.loop(seconds=30)
    async def valorantcycle(self):
        await self.bot.wait_until_ready()  # wait until the bot logs in
        channel = self.bot.get_channel(config['watch_channel']) # retrieves channel ID from config.json
        playerData = loadData()
        for user_id in playerData:
            user_data = playerData[user_id]
            if time.time() - user_data['lastTime'] > 5 * 60: # cooldown in seconds
                puuid = user_data['puuid']
                region = 'ap'
                name = user_data['name']
                tag = user_data['tag']
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'https://api.henrikdev.xyz/valorant/v3/matches/{region}/{name}/{tag}') as request:
                        # using this until access for riot granted async with session.get(f'https://{region}.api.riotgames.com/val/match/v1/matchlists/by-puuid/{puuid}?api_key={RIOT_TOKEN}') as request:
                        if request.status == 200:
                            data = await request.json()
                            if len(data['data']):
                                recentTime = data['data'][0]['metadata']['game_start']
                                if user_data['lastTime'] < recentTime: # if latest game played is more recent than stored latest
                                    embed = disnake.Embed(
                                        title="valorant watch",
                                        description=f"<@{user_id}> just finished a game!"
                                    )
                                    await channel.send(embed=embed)
                                    user_data['lastTime'] = recentTime
                                    saveData(playerData)
            await asyncio.sleep(1) # sleeps for number of seconds (avoid rate limit)
                          

def setup(bot: commands.Bot):
    bot.add_cog(Game(bot))
