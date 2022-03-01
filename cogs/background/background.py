import disnake
from disnake.ext import tasks, commands

import os
import json
import aiohttp
import asyncio
import time
import sys
import math
import random

from helpers import json_helper

# RIOT_TOKEN = os.environ["RIOT_TOKEN"] not used at the moment

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found!")
else:
    with open("config.json", encoding='utf-8') as file:
        config = json.load(file)

class Background(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.valorant_waitlist = {}
        self.valorant_watch_cycle.start()

    @tasks.loop(seconds=30)
    async def valorant_watch_cycle(self):
        await self.bot.wait_until_ready()  # wait until the bot logs in
        channel = self.bot.get_channel(config['watch_channel']) # retrieves channel ID from config.json
        playerData = json_helper.load()
        for user_id in playerData:
            playerData = json_helper.load() # reloads playerData 
            user_data = playerData[user_id]
            if time.time() - user_data['lastTime'] < config["watch_cooldown"] * 60: continue # cooldown in seconds
            puuid = user_data['puuid']
            region = user_data['region']
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://api.henrikdev.xyz/valorant/v3/by-puuid/matches/{region}/{puuid}') as request:
                    # using this until access for riot granted async with session.get(f'https://{region}.api.riotgames.com/val/match/v1/matchlists/by-puuid/{puuid}?api_key={RIOT_TOKEN}') as request:
                    if request.status != 200: continue
                    matchData = await request.json()
                for latestGame in matchData['data']:
                    startTime = latestGame['metadata']['game_start'] # given in s
                    duration = latestGame['metadata']['game_length'] / 1000 # given in ms 
                    recentTime = startTime + duration + 100
                    if user_data['lastTime'] >= recentTime: break # if stored latest is more recent than latest game played, break and skip user
                    mode = latestGame['metadata']['mode']
                    if mode == "Deathmatch": continue
                    party_red = []
                    party_blue = []
                    feeders = {}
                    rounds_played = rounds_red = rounds_blue = 0
                    for round in latestGame['rounds']:
                        rounds_played += round['end_type'] != "Surrendered"
                        rounds_red += round['winning_team'] == "Red"
                        rounds_blue += round['winning_team'] == "Blue"
                    for player in latestGame['players']['all_players']:
                        for player_id in playerData:
                            if player['puuid'] == playerData[player_id]['puuid']: # detects if multiple watched users are in the same game
                                kills = player['stats']['kills']
                                deaths = player['stats']['deaths']
                                assists = player['stats']['assists']
                                score = player['stats']['score']
                                team = player["team"]
                                if team == "Red":
                                    party_red.append(player_id)
                                elif team == "Blue":
                                    party_blue.append(player_id)
                                elif team == playerData[player_id]['puuid']: # deathmatch exception
                                    party_red.append(player_id)
                                map_played = latestGame["metadata"]["map"]
                                if deaths >= (kills + (1.1*math.e)**(kills/5) + 2.9): # formula for calculating feeding threshold
                                    feeders[player_id] = {
                                        "kills" : kills,
                                        "deaths" : deaths,
                                        "assists": assists,
                                        "acs": int(score/rounds_played),
                                        "kd" : "{:.2f}".format(kills/deaths)
                                    }
                    
                    async with session.get("https://api.henrikdev.xyz/valorant/v1/content") as mapRequest:
                        if mapRequest.status == 200:
                            mapData = await mapRequest.json()
                    for map in mapData["maps"]:
                        if map["name"] == map_played:
                            map_url = f"https://media.valorant-api.com/maps/{map['id']}/splash.png"
                            break

                    if rounds_red == rounds_blue: # draw
                        color = 0x767676
                        description = f"<@{'> and <@'.join(party_red+party_blue)}> just finished a {mode} game __**{rounds_red} - {rounds_blue}**__ on **{map_played}** <t:{int(recentTime)}:R>!"
                    elif party_red and party_blue: # watched players on both teams
                        color = 0x767676
                        description = f"<@{'> and <@'.join(party_red)}> just {'wonnered' if rounds_red > rounds_blue else 'losted'} a {mode} game __**{rounds_red} - {rounds_blue}**__ on **{map_played}** <t:{int(recentTime)}:R>! <@{'> and <@'.join(party_blue)}> played on the other team!"
                    elif party_red: # watched players on red only
                        color = 0x17dc33 if rounds_red > rounds_blue else 0xfc2828
                        description = f"<@{'> and <@'.join(party_red)}> just {'wonnered' if rounds_red > rounds_blue else 'losted'} a {mode} game __**{rounds_red} - {rounds_blue}**__ on **{map_played}** <t:{int(recentTime)}:R>!"
                    elif party_blue: # watched players on blue only
                        color = 0x17dc33 if rounds_blue > rounds_red else 0xfc2828
                        description = f"<@{'> and <@'.join(party_blue)}> just {'wonnered' if rounds_blue > rounds_red else 'losted'} a {mode} game __**{rounds_blue} - {rounds_red}**__ on **{map_played}** <t:{int(recentTime)}:R>!"
                    player_embed = disnake.Embed(
                        title="valorant watch",
                        color=color,
                        description=description
                    )
                    player_embed.set_thumbnail(
                        url=map_url
                    )
                    await channel.send(embed=player_embed) # sends the notification embed
                    
                    feeder_embed = disnake.Embed(
                        title="feeder alert❗❗",
                        color=0xff7614,
                        description=f"<@{'> and <@'.join(feeders.keys())}> inted! " + random.choice(config["feeder_msg"])
                    )
                    for feeder in feeders:
                        feeder_embed.add_field(
                            name="dirty inter",
                            value=f"<@{feeder}> finished {feeders[feeder]['kills']}/{feeders[feeder]['deaths']}/{feeders[feeder]['assists']} with an ACS of {feeders[feeder]['acs']}.",
                            inline=False
                        )
                    feeder_embed.set_image(
                        url=random.choice(config["feeder_embed_image"])
                    )
                    if feeders: await channel.send(embed=feeder_embed) # sends the feeder embed

                    combined_waiters = [] # init list of users to ping for waitlist
                    for member_id in party_red+party_blue:
                        # sets party members to update last updated time if more recent
                        if playerData[member_id]['lastTime'] < recentTime: playerData[member_id]['lastTime'] = recentTime
                        if member_id in self.bot.valorant_waitlist:
                            combined_waiters += self.bot.valorant_waitlist.pop(member_id)
                    if combined_waiters: await channel.send(f"<@{'> <@'.join(list(set(combined_waiters)))}> removing from waitlist") # pings waiters
                    
                    json_helper.save(playerData)
            await asyncio.sleep(0.5) # sleeps for number of seconds (avoid rate limit)

def setup(bot: commands.Bot):
    bot.add_cog(Background(bot))