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

class Background(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.valorantcycle.start()

    @tasks.loop(seconds=30)
    async def valorantcycle(self):
        await self.bot.wait_until_ready()  # wait until the bot logs in
        channel = self.bot.get_channel(config['watch_channel']) # retrieves channel ID from config.json
        playerData = json_helper.load()
        for user_id in playerData:
            playerData = json_helper.load()
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
                                    json_helper.save(playerData)
            await asyncio.sleep(0.5) # sleeps for number of seconds (avoid rate limit)
        
def setup(bot: commands.Bot):
    bot.add_cog(Background(bot))