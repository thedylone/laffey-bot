import disnake
from disnake.ext import tasks, commands

import aiohttp
import asyncio
import math
import random

from helpers import json_helper

# RIOT_TOKEN = os.environ["RIOT_TOKEN"] not used at the moment


class Background(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.valorant_waitlist = json_helper.load("waitlist.json")
        self.valorant_watch_cycle.start()

    @tasks.loop(seconds=30)
    async def valorant_watch_cycle(self):
        await self.bot.wait_until_ready()  # wait until the bot logs in
        init_list = [key for key in self.bot.player_data.keys()]
        for user_id in init_list:
            player_user = await self.bot.getch_user(int(user_id))
            if (
                player_user == None or user_id not in self.bot.player_data
            ):  # player no longer exists
                # del self.bot.player_data[user_id]
                # json_helper.save(self.bot.player_data, "playerData.json")
                continue
            user_data = self.bot.player_data[user_id]
            user_puuid = user_data["puuid"]
            user_region = user_data["region"]
            user_guild = user_data["guild"]
            channel = player_user
            channel_safe = False

            guild_exists = self.bot.get_guild(user_guild)
            if guild_exists in self.bot.guilds:
                # check if bot is still in the guild
                watch_channel_id = self.bot.guild_data[str(user_guild)]["watch_channel"]
                channel_exists = self.bot.get_channel(watch_channel_id)
                guild_exists_channels = guild_exists.text_channels
                if channel_exists in guild_exists_channels:
                    # check if channel is still in the guild
                    channel = channel_exists
                    channel_safe = True
                elif watch_channel_id:
                    # sends a warning that guild exists but channel is gone
                    self.bot.guild_data[str(user_guild)]["watch_channel"] = 0
                    json_helper.save(self.bot.guild_data, "guildData.json")
                    if guild_exists_channels:
                        await guild_exists_channels[0].send(
                            "The channel I am set to no longer exists! Please use valorant-setchannel on another channel. I will send updates to members directly instead."
                        )
            elif user_guild:
                # sends a DM to the user that bot is no longer in the guild
                user_data["guild"] = 0
                json_helper.save(self.bot.player_data, "playerData.json")
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
                        for player_id in self.bot.player_data:
                            if (
                                player_id == user_id
                                and player["puuid"] == user_puuid
                                or user_guild > 0
                                and player["puuid"]
                                == self.bot.player_data[player_id]["puuid"]
                                and self.bot.player_data[player_id]["guild"]
                                == user_guild
                            ):  # detects if multiple watched users who "watched" in the same guild (not 0) are in the same game
                                player_stats = player["stats"]
                                player_acs = player_stats["score"] / rounds_played
                                team = player["team"]
                                if team == "Red":
                                    party_red.append(player_id)
                                elif team == "Blue":
                                    party_blue.append(player_id)
                                elif (
                                    team == self.bot.player_data[player_id]["puuid"]
                                ):  # deathmatch exception
                                    party_red.append(player_id)

                                map_played = latest_game["metadata"]["map"]

                                if player_stats["deaths"] >= (
                                    player_stats["kills"]
                                    + (1.1 * math.e) ** (player_stats["kills"] / 5)
                                    + 2.9
                                ):  # formula for calculating feeding threshold
                                    feeders[player_id] = {
                                        "kills": player_stats["kills"],
                                        "deaths": player_stats["deaths"],
                                        "assists": player_stats["assists"],
                                        "acs": int(player_acs),
                                        "kd": "{:.2f}".format(
                                            player_stats["kills"]
                                            / player_stats["deaths"]
                                        ),
                                    }

                                if mode == "Competitive" or mode == "Unrated":
                                    # save stats
                                    self.bot.player_data[player_id][
                                        "headshots"
                                    ] = self.bot.player_data[player_id]["headshots"][
                                        -4:
                                    ] + [
                                        player_stats["headshots"]
                                    ]

                                    self.bot.player_data[player_id][
                                        "bodyshots"
                                    ] = self.bot.player_data[player_id]["bodyshots"][
                                        -4:
                                    ] + [
                                        player_stats["bodyshots"]
                                    ]

                                    self.bot.player_data[player_id][
                                        "legshots"
                                    ] = self.bot.player_data[player_id]["legshots"][
                                        -4:
                                    ] + [
                                        player_stats["legshots"]
                                    ]

                                    self.bot.player_data[player_id][
                                        "acs"
                                    ] = self.bot.player_data[player_id]["acs"][-4:] + [
                                        player_acs
                                    ]

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

                    if feeders:
                        feeder_messages = ["lmao", "git gud"]
                        feeder_images = [
                            "https://intinc.com/wp-content/uploads/2022/02/INT-Logo-Update_2104.png"
                        ]
                        if user_guild != 0 and str(user_guild) in self.bot.guild_data:
                            if (
                                "feeder_messages"
                                in self.bot.guild_data[str(user_guild)]
                                and self.bot.guild_data[str(user_guild)][
                                    "feeder_messages"
                                ]
                            ):
                                feeder_messages = self.bot.guild_data[str(user_guild)][
                                    "feeder_messages"
                                ]
                            if (
                                "feeder_images" in self.bot.guild_data[str(user_guild)]
                                and self.bot.guild_data[str(user_guild)][
                                    "feeder_images"
                                ]
                            ):
                                feeder_images = self.bot.guild_data[str(user_guild)][
                                    "feeder_images"
                                ]

                        feeder_values = []
                        for feeder in feeders:
                            feeder_values += [
                                f"<@{feeder}> finished {feeders[feeder]['kills']}/{feeders[feeder]['deaths']}/{feeders[feeder]['assists']} with an ACS of {feeders[feeder]['acs']}."
                            ]
                        player_embed.add_field(
                            name=f"feeder alert❗❗ {random.choice(feeder_messages)}",
                            value="\n".join(feeder_values),
                            inline=False,
                        )
                        player_embed.set_image(url=random.choice(feeder_images))

                    combined_waiters = []  # init list of users to ping for waitlist

                    streak_values = []

                    for member_id in party_red:
                        # streak function
                        if rounds_red != rounds_blue:
                            if rounds_red > rounds_blue:
                                new_streak = max(
                                    self.bot.player_data[member_id]["streak"] + 1, 1
                                )
                            elif rounds_red < rounds_blue:
                                new_streak = min(
                                    self.bot.player_data[member_id]["streak"] - 1, -1
                                )
                            if abs(new_streak) >= 3:
                                streak_values += [
                                    f"<@{member_id}> is on a {abs(new_streak)}-game {'winning' if new_streak > 0 else 'losing'} streak!"
                                ]
                            self.bot.player_data[member_id]["streak"] = new_streak

                        # sets party members to update last updated time if more recent
                        self.bot.player_data[member_id]["lastTime"] = max(
                            self.bot.player_data[member_id]["lastTime"], recent_time
                        )
                        if member_id in self.bot.valorant_waitlist:
                            combined_waiters += self.bot.valorant_waitlist.pop(
                                member_id
                            )

                    for member_id in party_blue:
                        # streak function
                        if rounds_red != rounds_blue:
                            if rounds_blue > rounds_red:
                                new_streak = max(
                                    self.bot.player_data[member_id]["streak"] + 1, 1
                                )
                            elif rounds_blue < rounds_red:
                                new_streak = min(
                                    self.bot.player_data[member_id]["streak"] - 1, -1
                                )
                            if abs(new_streak) >= 3:
                                streak_values += [
                                    f"<@{member_id}> is on a {abs(new_streak)}-game {'winning' if new_streak > 0 else 'losing'} streak!"
                                ]
                            self.bot.player_data[member_id]["streak"] = new_streak

                        # sets party members to update last updated time if more recent
                        self.bot.player_data[member_id]["lastTime"] = max(
                            self.bot.player_data[member_id]["lastTime"], recent_time
                        )
                        if member_id in self.bot.valorant_waitlist:
                            combined_waiters += self.bot.valorant_waitlist.pop(
                                member_id
                            )

                    if streak_values:
                        streak_messages = ["butt ass naked", "cock"]
                        if user_guild != 0 and str(user_guild) in self.bot.guild_data:
                            if (
                                "streak_messages"
                                in self.bot.guild_data[str(user_guild)]
                                and self.bot.guild_data[str(user_guild)][
                                    "streak_messages"
                                ]
                            ):
                                feeder_messages = self.bot.guild_data[str(user_guild)][
                                    "streak_messages"
                                ]
                        player_embed.add_field(
                            name=f"streaker alert 👀👀 {random.choice(streak_messages)}",
                            value="\n".join(streak_values),
                            inline=False,
                        )

                    content = ""

                    if combined_waiters:
                        if channel_safe:
                            content = (
                                f"removing <@{'> <@'.join(list(set(combined_waiters)))}> from waitlist",
                            )
                        else:
                            for waiter in list(set(combined_waiters)):
                                waiter_user = await self.bot.getch_user(waiter)
                                if waiter_user:
                                    content = (
                                        "A player you were waiting for is done!",
                                    )
                        json_helper.save(self.bot.valorant_waitlist, "waitlist.json")

                    await channel.send(
                        content=content,
                        embed=player_embed,
                    )
                    json_helper.save(self.bot.player_data, "playerData.json")

            await asyncio.sleep(0.5)  # sleeps for number of seconds (avoid rate limit)


def setup(bot: commands.Bot):
    bot.add_cog(Background(bot))
