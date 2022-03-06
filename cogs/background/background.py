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
    with open("config.json", encoding="utf-8") as file:
        config = json.load(file)


class Background(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.valorant_waitlist = {}
        self.valorant_watch_cycle.start()

    @tasks.loop(seconds=30)
    async def valorant_watch_cycle(self):
        await self.bot.wait_until_ready()  # wait until the bot logs in
        player_data = json_helper.load("playerData.json")
        init_list = [key for key in player_data.keys()]
        for user_id in init_list:
            player_user = await self.bot.getch_user(int(user_id))
            if player_user == None:  # player no longer exists
                # del player_data[user_id] 
                # json_helper.save(player_data, "playerData.json")
                continue
            player_data = json_helper.load("playerData.json")  # reloads player_data
            guild_data = json_helper.load("guildData.json")
            user_data = player_data[user_id]
            user_puuid = user_data["puuid"]
            user_region = user_data["region"]
            user_guild = user_data["guild"]
            channel = player_user
            channel_safe = False

            guild_exists = self.bot.get_guild(user_guild)
            if guild_exists in self.bot.guilds:
                # check if bot is still in the guild
                watch_channel_id = guild_data[str(user_guild)]["watch_channel"]
                channel_exists = self.bot.get_channel(watch_channel_id)
                guild_exists_channels = guild_exists.text_channels
                if channel_exists in guild_exists_channels:
                    # check if channel is still in the guild
                    channel = channel_exists
                    channel_safe = True
                elif watch_channel_id:
                    # sends a warning that guild exists but channel is gone
                    guild_data[str(user_guild)]["watch_channel"] = 0
                    json_helper.save(guild_data, "guildData.json")
                    if guild_exists_channels:
                        await guild_exists_channels[0].send(
                            "The channel I am set to no longer exists! Please use valorant-setchannel on another channel. I will send updates to members directly instead."
                        )
            elif user_guild:
                # sends a DM to the user that bot is no longer in the guild
                user_data["guild"] = 0
                json_helper.save(player_data, "playerData.json")
                await player_user.send(
                    "I am no longer in the server you initialised valorant-watch in. I will send updates to you directly. Alternatively, you can /valorant-unwatch to stop receiving updates, or perform /valorant-watch in another server."
                )

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.henrikdev.xyz/valorant/v3/by-puuid/matches/{user_region}/{user_puuid}"
                ) as match_request:
                    # using this until access for riot granted async with session.get(f'https://{region}.api.riotgames.com/val/match/v1/matchlists/by-puuid/{puuid}?api_key={RIOT_TOKEN}') as request:
                    if match_request.status != 200:
                        continue
                    match_data = await match_request.json()
                for latest_game in match_data["data"]:
                    start_time = latest_game["metadata"]["game_start"]  # given in s
                    duration = (
                        latest_game["metadata"]["game_length"] / 1000
                    )  # given in ms
                    recent_time = start_time + duration + 100
                    if user_data["lastTime"] >= recent_time:
                        break  # if stored latest is more recent than latest game played, break and skip user
                    mode = latest_game["metadata"]["mode"]
                    if mode == "Deathmatch":
                        continue
                    party_red = []
                    party_blue = []
                    feeders = {}
                    rounds_played = rounds_red = rounds_blue = 0
                    is_surrendered = False
                    for round in latest_game["rounds"]:
                        if round["end_type"] == "Surrendered":
                            is_surrendered = True
                        else:
                            rounds_played += 1
                        rounds_red += round["winning_team"] == "Red"
                        rounds_blue += round["winning_team"] == "Blue"
                    for player in latest_game["players"]["all_players"]:
                        for player_id in player_data:
                            if (
                                player_id == user_id
                                and player["puuid"] == user_puuid
                                or user_guild > 0
                                and player["puuid"] == player_data[player_id]["puuid"]
                                and player_data[player_id]["guild"] == user_guild
                            ):  # detects if multiple watched users who "watched" in the same guild (not 0) are in the same game
                                kills = player["stats"]["kills"]
                                deaths = player["stats"]["deaths"]
                                assists = player["stats"]["assists"]
                                score = player["stats"]["score"]
                                team = player["team"]
                                if team == "Red":
                                    party_red.append(player_id)
                                elif team == "Blue":
                                    party_blue.append(player_id)
                                elif (
                                    team == player_data[player_id]["puuid"]
                                ):  # deathmatch exception
                                    party_red.append(player_id)
                                map_played = latest_game["metadata"]["map"]
                                if deaths >= (
                                    kills + (1.1 * math.e) ** (kills / 5) + 2.9
                                ):  # formula for calculating feeding threshold
                                    feeders[player_id] = {
                                        "kills": kills,
                                        "deaths": deaths,
                                        "assists": assists,
                                        "acs": int(score / rounds_played),
                                        "kd": "{:.2f}".format(kills / deaths),
                                    }

                    async with session.get(
                        "https://api.henrikdev.xyz/valorant/v1/content"
                    ) as map_request:
                        if map_request.status == 200:
                            map_data = await map_request.json()
                    for map in map_data["maps"]:
                        if map["name"] == map_played:
                            map_url = f"https://media.valorant-api.com/maps/{map['id']}/splash.png"
                            break

                    if rounds_red == rounds_blue:  # draw
                        color = 0x767676
                        description = f"<@{'> and <@'.join(party_red+party_blue)}> just finished a {mode} game __**{rounds_red} - {rounds_blue}**__ on **{map_played}** <t:{int(recent_time)}:R>!"
                    elif party_red and party_blue:  # watched players on both teams
                        color = 0x767676
                        description = f"<@{'> and <@'.join(party_red)}> just {'wonnered' if rounds_red > rounds_blue else 'losted'} a {mode} game __**{rounds_red} - {rounds_blue}**__ {'(surrendered) ' if is_surrendered else ' '}on **{map_played}** <t:{int(recent_time)}:R>! <@{'> and <@'.join(party_blue)}> played on the other team!"
                    elif party_red:  # watched players on red only
                        color = 0x17DC33 if rounds_red > rounds_blue else 0xFC2828
                        description = f"<@{'> and <@'.join(party_red)}> just {'wonnered' if rounds_red > rounds_blue else 'losted'} a {mode} game __**{rounds_red} - {rounds_blue}**__ {'(surrendered) ' if is_surrendered else ' '}on **{map_played}** <t:{int(recent_time)}:R>!"
                    elif party_blue:  # watched players on blue only
                        color = 0x17DC33 if rounds_blue > rounds_red else 0xFC2828
                        description = f"<@{'> and <@'.join(party_blue)}> just {'wonnered' if rounds_blue > rounds_red else 'losted'} a {mode} game __**{rounds_blue} - {rounds_red}**__ {'(surrendered) ' if is_surrendered else ' '}on **{map_played}** <t:{int(recent_time)}:R>!"
                    player_embed = disnake.Embed(
                        title="valorant watch", color=color, description=description
                    )
                    player_embed.set_thumbnail(url=map_url)
                    await channel.send(
                        embed=player_embed
                    )  # sends the notification embed

                    if feeders:
                        if user_guild == 0 or str(user_guild) not in guild_data or "feeder_messages" not in guild_data[str(user_guild)]:
                            feeder_messages = ["lmao", "git gud"]
                        else:
                            feeder_messages = guild_data[str(user_guild)]["feeder_messages"]
                        feeder_embed = disnake.Embed(
                            title="feeder alert❗❗",
                            color=0xFF7614,
                            description=f"<@{'> and <@'.join(feeders.keys())}> inted! {random.choice(feeder_messages)}",
                        )
                        for feeder in feeders:
                            feeder_embed.add_field(
                                name="dirty inter",
                                value=f"<@{feeder}> finished {feeders[feeder]['kills']}/{feeders[feeder]['deaths']}/{feeders[feeder]['assists']} with an ACS of {feeders[feeder]['acs']}.",
                                inline=False,
                            )
                        feeder_embed.set_image(
                            url=random.choice(config["feeder_embed_image"])
                        )
                        await channel.send(embed=feeder_embed)  # sends the feeder embed

                    combined_waiters = []  # init list of users to ping for waitlist

                    is_streak = False
                    streak_embed = disnake.Embed(
                        title="streaker alert 👀👀",
                        color=0xCC36D1,
                        description="someone is on a streak!",
                    )

                    for member_id in party_red:
                        # streak function
                        if rounds_red > rounds_blue:
                            new_streak = max(player_data[member_id]["streak"] + 1, 1)
                        elif rounds_red < rounds_blue:
                            new_streak = min(player_data[member_id]["streak"] - 1, -1)
                        if abs(new_streak) >= 3:
                            is_streak = True
                            streak_embed.add_field(
                                name="streaker",
                                value=f"<@{member_id}> is on a {abs(new_streak)}-game {'winning' if new_streak > 0 else 'losing'} streak!",
                            )
                        player_data[member_id]["streak"] = new_streak

                        # sets party members to update last updated time if more recent
                        player_data[member_id]["lastTime"] = max(
                            player_data[member_id]["lastTime"], recent_time
                        )
                        if member_id in self.bot.valorant_waitlist:
                            combined_waiters += self.bot.valorant_waitlist.pop(
                                member_id
                            )

                    for member_id in party_blue:
                        # streak function
                        if rounds_blue > rounds_red:
                            new_streak = max(player_data[member_id]["streak"] + 1, 1)
                        elif rounds_blue < rounds_red:
                            new_streak = min(player_data[member_id]["streak"] - 1, -1)
                        if abs(new_streak) >= 3:
                            is_streak = True
                            streak_embed.add_field(
                                name="streaker",
                                value=f"<@{member_id}> is on a {abs(new_streak)}-game {'winning' if new_streak > 0 else 'losing'} streak!",
                                inline=False,
                            )
                        player_data[member_id]["streak"] = new_streak

                        # sets party members to update last updated time if more recent
                        player_data[member_id]["lastTime"] = max(
                            player_data[member_id]["lastTime"], recent_time
                        )
                        if member_id in self.bot.valorant_waitlist:
                            combined_waiters += self.bot.valorant_waitlist.pop(
                                member_id
                            )

                    if is_streak:
                        await channel.send(embed=streak_embed)

                    if combined_waiters:
                        if channel_safe:
                            await channel.send(
                                f"<@{'> <@'.join(list(set(combined_waiters)))}> removing from waitlist"
                            )  # pings waiters in same channel
                        else:
                            for waiter in list(set(combined_waiters)):
                                waiter_user = await self.bot.getch_user(waiter)
                                if waiter_user:
                                    await waiter_user.send(
                                        "A player you were waiting for is done!"
                                    )

                    json_helper.save(player_data, "playerData.json")
            await asyncio.sleep(0.5)  # sleeps for number of seconds (avoid rate limit)


def setup(bot: commands.Bot):
    bot.add_cog(Background(bot))
