import disnake
from disnake.ext import tasks, commands

import aiohttp
import asyncio
import math
import random

from helpers import db_helper

# RIOT_TOKEN = os.environ["RIOT_TOKEN"] not used at the moment


class Background(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.valorant_watch_cycle = self.valorant_watch_cycle

    @tasks.loop()
    async def valorant_watch_cycle(self):
        await self.bot.wait_until_ready()  # wait until the bot logs in
        init_list = list(
            map(
                lambda x: x.get("player_id"),
                await self.bot.db.fetch("select player_id from players"),
            )
        )
        for user_id in init_list:
            player_user = await self.bot.getch_user(user_id)
            if player_user == None or user_id not in list(
                map(
                    lambda x: x.get("player_id"),
                    await self.bot.db.fetch("select player_id from players"),
                )
            ):  # player no longer exists
                # await db_helper.delete_player_data(self.bot, user_id)
                continue
            user_data = await db_helper.get_player_data(self.bot, user_id)
            if len(user_data) == 0:
                continue
            user_data = user_data[0]
            user_puuid = user_data["puuid"]
            user_region = user_data["region"]
            user_guild = user_data["guild_id"]
            channel = player_user
            channel_safe = False

            guild_exists = self.bot.get_guild(user_guild)
            guild_data = await db_helper.get_guild_data(self.bot, user_guild)
            if guild_exists in self.bot.guilds and len(guild_data):
                # check if bot is still in the guild
                watch_channel_id = guild_data[0].get("watch_channel")
                channel_exists = self.bot.get_channel(watch_channel_id)
                guild_exists_channels = guild_exists.text_channels
                if channel_exists in guild_exists_channels:
                    # check if channel is still in the guild
                    channel = channel_exists
                    channel_safe = True
                elif watch_channel_id:
                    # sends a warning that guild exists but channel is gone
                    await db_helper.update_guild_data(
                        self.bot, user_guild, watch_channel=0
                    )
                    if guild_exists_channels:
                        await guild_exists_channels[0].send(
                            "The channel I am set to no longer exists! Please use setchannel on another channel. I will send updates to members directly instead."
                        )
            elif user_guild:
                # sends a DM to the user that bot is no longer in the guild
                user_guild = 0
                await db_helper.update_player_data(self.bot, user_id, guild_id=0)
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
                    user_data = await db_helper.get_player_data(self.bot, user_id)
                    if len(user_data) == 0:
                        break
                    user_data = user_data[0]
                    if user_data["lasttime"] >= recent_time:
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
                        for player_id in init_list:
                            player_data = await db_helper.get_player_data(
                                self.bot, player_id
                            )
                            if (
                                player_id == user_id
                                and player["puuid"] == user_puuid
                                or user_guild > 0
                                and len(player_data)
                                and player["puuid"] == player_data[0]["puuid"]
                                and player_data[0]["guild_id"] == user_guild
                            ):  # detects if multiple watched users who "watched" in the same guild (not 0) are in the same game
                                player_stats = player["stats"]
                                player_acs = player_stats["score"] / rounds_played
                                team = player["team"]
                                if team == "Red":
                                    party_red.append(player_id)
                                elif team == "Blue":
                                    party_blue.append(player_id)
                                else:  # deathmatch exception
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
                                    await db_helper.update_player_data(
                                        self.bot,
                                        player_id,
                                        headshots=player_data[0]["headshots"][-4:]
                                        + [player_stats["headshots"]],
                                        bodyshots=player_data[0]["bodyshots"][-4:]
                                        + [player_stats["bodyshots"]],
                                        legshots=player_data[0]["legshots"][-4:]
                                        + [player_stats["legshots"]],
                                        acs=player_data[0]["acs"][-4:] + [player_acs],
                                    )

                    async with session.get(
                        "https://api.henrikdev.xyz/valorant/v1/content"
                    ) as map_request:
                        if map_request.status == 200:
                            map_data = await map_request.json()
                    for map_res in map_data["maps"]:
                        if map_res["name"] == map_played:
                            map_url = f"https://media.valorant-api.com/maps/{map_res['id']}/splash.png"
                            break

                    if rounds_red == rounds_blue:  # draw
                        color = 0x767676
                        description = f"<@{'> and <@'.join(map(str, party_red+party_blue))}> just finished a {mode} game __**{rounds_red} - {rounds_blue}**__ on **{map_played}** <t:{int(recent_time)}:R>!"
                    elif party_red and party_blue:  # watched players on both teams
                        color = 0x767676
                        description = f"<@{'> and <@'.join(map(str,party_red))}> just {'wonnered' if rounds_red > rounds_blue else 'losted'} a {mode} game __**{rounds_red} - {rounds_blue}**__ {'(surrendered) ' if is_surrendered else ' '}on **{map_played}** <t:{int(recent_time)}:R>! <@{'> and <@'.join(map(str,party_blue))}> played on the other team!"
                    elif party_red:  # watched players on red only
                        color = 0x17DC33 if rounds_red > rounds_blue else 0xFC2828
                        description = f"<@{'> and <@'.join(map(str,party_red))}> just {'wonnered' if rounds_red > rounds_blue else 'losted'} a {mode} game __**{rounds_red} - {rounds_blue}**__ {'(surrendered) ' if is_surrendered else ' '}on **{map_played}** <t:{int(recent_time)}:R>!"
                    elif party_blue:  # watched players on blue only
                        color = 0x17DC33 if rounds_blue > rounds_red else 0xFC2828
                        description = f"<@{'> and <@'.join(map(str,party_blue))}> just {'wonnered' if rounds_blue > rounds_red else 'losted'} a {mode} game __**{rounds_blue} - {rounds_red}**__ {'(surrendered) ' if is_surrendered else ' '}on **{map_played}** <t:{int(recent_time)}:R>!"
                    player_embed = disnake.Embed(
                        title="valorant watch", color=color, description=description
                    )
                    player_embed.set_thumbnail(url=map_url)
                    guild_data = await db_helper.get_guild_data(self.bot, user_guild)
                    if feeders:
                        feeder_messages = ["lmao", "git gud"]
                        feeder_images = [
                            "https://intinc.com/wp-content/uploads/2022/02/INT-Logo-Update_2104.png"
                        ]
                        guild_data = await db_helper.get_guild_data(
                            self.bot, user_guild
                        )
                        if len(guild_data) and guild_data[0].get("feeder_messages"):
                            feeder_messages = guild_data[0].get("feeder_messages")
                        if len(guild_data) and guild_data[0].get("feeder_images"):
                            feeder_images = guild_data[0].get("feeder_images")

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
                        member_data = await db_helper.get_player_data(
                            self.bot, member_id
                        )
                        if len(member_data) and rounds_red != rounds_blue:
                            if rounds_red > rounds_blue:
                                new_streak = max(member_data[0]["streak"] + 1, 1)
                            elif rounds_red < rounds_blue:
                                new_streak = min(member_data[0]["streak"] - 1, -1)
                            if abs(new_streak) >= 3:
                                streak_values += [
                                    f"<@{member_id}> is on a {abs(new_streak)}-game {'winning' if new_streak > 0 else 'losing'} streak!"
                                ]
                            await db_helper.update_player_data(
                                self.bot, member_id, streak=new_streak
                            )

                        # sets party members to update last updated time if more recent
                        if recent_time > member_data[0].get("lasttime"):
                            await db_helper.update_player_data(
                                self.bot, member_id, lasttime=recent_time
                            )

                        waitlist_data = await db_helper.get_waitlist_data(
                            self.bot, member_id
                        )
                        if len(waitlist_data):
                            combined_waiters += waitlist_data[0].get("waiting_id")
                            await db_helper.delete_waitlist_data(self.bot, member_id)

                    for member_id in party_blue:
                        # streak function
                        member_data = await db_helper.get_player_data(
                            self.bot, member_id
                        )
                        if len(member_data) and rounds_red != rounds_blue:
                            if rounds_blue > rounds_red:
                                new_streak = max(member_data[0]["streak"] + 1, 1)
                            elif rounds_blue < rounds_red:
                                new_streak = min(member_data[0]["streak"] - 1, -1)
                            if abs(new_streak) >= 3:
                                streak_values += [
                                    f"<@{member_id}> is on a {abs(new_streak)}-game {'winning' if new_streak > 0 else 'losing'} streak!"
                                ]
                            await db_helper.update_player_data(
                                self.bot, member_id, streak=new_streak
                            )

                        # sets party members to update last updated time if more recent
                        if recent_time > member_data[0].get("lasttime"):
                            await db_helper.update_player_data(
                                self.bot, member_id, lasttime=recent_time
                            )

                        waitlist_data = await db_helper.get_waitlist_data(
                            self.bot, member_id
                        )
                        if len(waitlist_data):
                            combined_waiters += waitlist_data[0].get("waiting_id")
                            await db_helper.delete_waitlist_data(self.bot, member_id)

                    if streak_values:
                        streaker_messages = ["butt ass naked", "wow streak"]
                        if len(guild_data) and guild_data[0].get("streaker_messages"):
                            streaker_messages = guild_data[0].get("streaker_messages")
                        player_embed.add_field(
                            name=f"streaker alert 👀👀 {random.choice(streaker_messages)}",
                            value="\n".join(streak_values),
                            inline=False,
                        )

                    content = ""

                    if combined_waiters:
                        if channel_safe:
                            await channel.send(
                                content=f"removing <@{'> <@'.join(map(str,(set(combined_waiters))))}> from waitlist",
                                embed=player_embed,
                            )
                        else:
                            for waiter in list(set(combined_waiters)):
                                waiter_user = await self.bot.getch_user(waiter)
                                if waiter_user:
                                    await channel.send(
                                        content="A player you were waiting for is done!",
                                        embed=player_embed,
                                    )
                                    break
                    else:
                        await channel.send(
                            embed=player_embed,
                        )

            await asyncio.sleep(0.5)  # sleeps for number of seconds (avoid rate limit)


def setup(bot: commands.Bot):
    bot.add_cog(Background(bot))
