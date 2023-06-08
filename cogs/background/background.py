"""background tasks"""
import asyncio
import math
import random
import aiohttp

import disnake
from disnake.ext import tasks, commands


from helpers import db_helper

session = aiohttp.ClientSession()


class ValorantMatchBackground:
    def __init__(
        self,
        bot,
        discord_id,
        puuid,
        guild,
        guild_data,
        channel,
        channel_safe,
        game,
        recent_time,
        mode,
        map_played,
        map_url,
    ):
        self.bot = bot
        self.discord_id = discord_id
        self.puuid = puuid
        self.guild = guild
        self.guild_data = guild_data
        self.channel = channel
        self.channel_safe = channel_safe
        self.game = game
        self.recent_time = recent_time
        self.mode = mode
        self.map_played = map_played
        self.map_url = map_url
        self.party_red = []
        self.party_blue = []
        self.feeders = {}
        self.rounds_total = 0
        self.rounds_red = 0
        self.rounds_blue = 0
        self.is_surrendered = False
        self.cycle_discord_id = None
        self.cycle_data = None
        self.player_embed = disnake.Embed(
            title="valorant watch"
        ).set_thumbnail(map_url)
        self.streak_values = []
        self.combined_waiters = []

    async def get_player_data_from_db(self, puuid):
        return await self.bot.db.fetch(
            "select * from players where puuid = $1", puuid
        )

    async def check_player_is_current_or_in_db(self, player):
        """
        returns True if player_puuid is self.puuid,
        or if player_puuid in database and has same guild as self.guild
        """
        player_puuid = player.get("puuid")
        if player_puuid == self.puuid:
            db_data = await self.get_player_data_from_db(self.puuid)
            self.cycle_data = db_data[0]
            self.cycle_discord_id = self.discord_id
            return True
        if self.guild == 0:
            return False
        db_data = await self.get_player_data_from_db(player_puuid)
        if len(db_data) > 0 and db_data[0].get("guild_id") == self.guild:
            self.cycle_data = db_data[0]
            self.cycle_discord_id = db_data[0].get("player_id")
            return True
        return False

    def add_to_rounds(self):
        for round in self.game.get("rounds"):
            if round.get("end_type") == "Surrendered":
                self.is_surrendered = True
            else:
                self.rounds_total += 1
            self.rounds_red += round.get("winning_team") == "Red"
            self.rounds_blue += round.get("winning_team") == "Blue"

    def check_triggrering_feeder(self, deaths, kills):
        """returns True is feeder is triggered"""
        return deaths >= (kills + (1.1 * math.e) ** (kills / 5) + 2.9)

    @staticmethod
    def mention_list(mention_list):
        """joins a list into discord mentions"""
        return f"<@{'> and <@'.join(map(str, mention_list))}>"

    def rounds_to_player_embed(self):
        """convert rounds into a player embed"""
        action = {
            "win": f"just wonnered a {self.mode} game",
            "lose": f"just losted a {self.mode} game",
            "draw": f"just finished a {self.mode} game",
        }
        scores = {
            "red": f"__**{self.rounds_red} - {self.rounds_blue}**__",
            "blue": f"__**{self.rounds_blue} - {self.rounds_red}**__",
        }
        surr = "(surrendered) " if self.is_surrendered else None
        on_map = f"on **{self.map_played}**"
        timestamp = f"<t:{int(self.recent_time)}:R>!"
        extra = None
        if self.rounds_red == self.rounds_blue:
            # draw
            players = self.mention_list(self.party_red + self.party_blue)
            act = "draw"
            team = "red"
            color = 0x767676
        elif self.party_red and self.party_blue:
            # watched players on both teams
            players = self.mention_list(self.party_red)
            act = "win" if self.rounds_red > self.rounds_blue else "lose"
            team = "red"
            color = 0x767676
            extra_players = self.mention_list(self.party_blue)
            extra = f" {extra_players} played on the other team!"
        elif self.party_red:  # watched players on red only
            won = self.rounds_red > self.rounds_blue
            players = self.mention_list(self.party_red)
            act = "win" if won else "lose"
            team = "red"
            color = 0x17DC33 if won else 0xFC2828
        elif self.party_blue:  # watched players on blue only
            won = self.rounds_blue > self.rounds_red
            players = self.mention_list(self.party_blue)
            act = "win" if won else "lose"
            team = "blue"
            color = 0x17DC33 if won else 0xFC2828
        strings = [
            players,
            action[act],
            scores[team],
            surr,
            on_map,
            timestamp,
            extra,
        ]
        self.player_embed.description = " ".join(filter(None, strings))
        self.player_embed.color = color

    def feeders_to_player_embed(self):
        """adds feeders info to player embed if there are any feeders"""
        if not self.feeders:
            return
        # default messages and images
        feeder_messages = ["lmao", "git gud"]
        feeder_images = [
            "https://i.ytimg.com/vi/PZe1FbclgpM/maxresdefault.jpg"
        ]
        # retrieve guild's custom if set
        if len(self.guild_data) and self.guild_data[0].get("feeder_messages"):
            feeder_messages = self.guild_data[0].get("feeder_messages")
        if len(self.guild_data) and self.guild_data[0].get("feeder_images"):
            feeder_images = self.guild_data[0].get("feeder_images")

        feeder_values = []
        for feeder in self.feeders:
            feeder_dict = self.feeders[feeder]
            k = feeder_dict.get("kills")
            d = feeder_dict.get("deaths")
            a = feeder_dict.get("assists")
            acs = feeder_dict.get("acs")
            feeder_values.append(
                f"<@{feeder}> finished {k}/{d}/{a} with an ACS of {acs}."
            )

        self.player_embed.add_field(
            name=f"feeder alert❗❗ {random.choice(feeder_messages)}",
            value="\n".join(feeder_values),
            inline=False,
        )
        self.player_embed.set_image(url=random.choice(feeder_images))

    async def update_player_streak(self, id, member_data, win):
        """updates database for streak"""
        if self.rounds_red == self.rounds_blue:
            return
        if win:
            new_streak = max(member_data[0].get("streak") + 1, 1)
        else:
            new_streak = min(member_data[0].get("streak") - 1, -1)
        if abs(new_streak) >= 3:
            streaktype = "winning" if new_streak > 0 else "losing"
            self.streak_values.append(
                f"<@{id}> is on a {abs(new_streak)}-game {streaktype} streak!"
            )
        await db_helper.update_player_data(self.bot, id, streak=new_streak)

    async def update_player_lasttime(self, id, member_data):
        """updates database lasttime if more recent"""
        if self.recent_time > member_data[0].get("lasttime"):
            await db_helper.update_player_data(
                self.bot,
                id,
                lasttime=self.recent_time,
            )

    async def update_player_waitlist(self, id):
        """updates database waitlist and adds to list of waiters"""
        waitlist_data = await db_helper.get_waitlist_data(self.bot, id)
        if len(waitlist_data):
            self.combined_waiters += waitlist_data[0].get("waiting_id")
            await db_helper.delete_waitlist_data(self.bot, id)

    def streakers_to_player_embed(self):
        """adds streakers info to player embed if there are any streakers"""
        if not self.streak_values:
            return
        # default messages
        streaker_messages = ["butt ass naked", "wow streak"]
        # retrieve guild's custom if set
        data = self.guild_data
        if len(data) and data[0].get("streaker_messages"):
            streaker_messages = data[0].get("streaker_messages")

        self.player_embed.add_field(
            name=f"streaker alert 👀👀 {random.choice(streaker_messages)}",
            value="\n".join(self.streak_values),
            inline=False,
        )

    async def waitlist_to_content(self):
        """returns content to send if there are any waiters"""
        content = ""
        if not self.combined_waiters:
            return content
        # remove duplicates
        waiters = list(set(self.combined_waiters))
        if self.channel_safe:
            # able to send to a guild's channel
            waiters = self.mention_list(waiters)
            content = f"removing {waiters}> from waitlist"
        else:
            for waiter in waiters:
                waiter_user = await self.bot.getch_user(waiter)
                if waiter_user:
                    # user exists and accessible by bot
                    content = "A player you were waiting for is done!"
        return content

    async def main(self):
        self.add_to_rounds()
        for player in self.game["players"].get("all_players"):
            if not await self.check_player_is_current_or_in_db(player):
                continue
            player_stats = player.get("stats")
            player_acs = player_stats.get("score") / self.rounds_total
            team = player.get("team")
            if team == "Red":
                self.party_red.append(self.cycle_discord_id)
            elif team == "Blue":
                self.party_blue.append(self.cycle_discord_id)
            else:
                self.party_red.append(self.cycle_discord_id)

            kills = player_stats.get("kills")
            deaths = player_stats.get("deaths")
            if self.check_triggrering_feeder(deaths, kills):
                # add to feeders dictionary
                self.feeders[self.cycle_discord_id] = {
                    "kills": kills,
                    "deaths": deaths,
                    "assists": player_stats.get("assists"),
                    "acs": int(player_acs),
                    "kd": f"{kills / deaths:.2f}",
                }

            if self.mode in ("Competitive", "Unrated"):
                # save stats
                await db_helper.update_player_data(
                    self.bot,
                    self.cycle_discord_id,
                    headshots=self.cycle_data.get("headshots")[-4:]
                    + [player_stats.get("headshots")],
                    bodyshots=self.cycle_data.get("bodyshots")[-4:]
                    + [player_stats.get("bodyshots")],
                    legshots=self.cycle_data.get("legshots")[-4:]
                    + [player_stats.get("legshots")],
                    acs=self.cycle_data.get("acs")[-4:] + [player_acs],
                )

        self.rounds_to_player_embed()

        self.feeders_to_player_embed()

        for member_id in self.party_red:
            member_data = await db_helper.get_player_data(self.bot, member_id)
            if len(member_data) == 0:
                continue
            win = self.rounds_red > self.rounds_blue
            await self.update_player_streak(member_id, member_data, win)
            await self.update_player_lasttime(member_id, member_data)
            await self.update_player_waitlist(member_id)

        for member_id in self.party_blue:
            member_data = await db_helper.get_player_data(self.bot, member_id)
            if len(member_data) == 0:
                continue
            win = self.rounds_blue > self.rounds_red
            await self.update_player_streak(member_id, member_data, win)
            await self.update_player_lasttime(member_id, member_data)
            await self.update_player_waitlist(member_id)

        self.streakers_to_player_embed()
        content = await self.waitlist_to_content()

        await self.channel.send(
            content=content,
            embed=self.player_embed,
        )


class ValorantBackground:

    matches_url = "https://api.henrikdev.xyz/valorant/v3/by-puuid/matches"
    maps_url = "https://api.henrikdev.xyz/valorant/v1/content"

    def __init__(self, bot, discord_id):
        self.bot = bot
        self.discord_id = discord_id
        self.discord_user = None
        self.user_db_data = None
        self.guild_data = None
        self.puuid = None
        self.region = None
        self.channel = None
        self.guild = None
        self.channel_safe = False
        self.recent_time = None

    async def get_player_id_from_db(self):
        """retrieve player_ids from players db"""
        db_players = await self.bot.db.fetch("select player_id from players")
        return list(map(lambda x: x.get("player_id"), db_players))

    async def check_current_user_exists(self):
        """returns True if user exists in database and as Discord user"""
        db_players_id = await self.get_player_id_from_db()
        if self.discord_id not in db_players_id:
            return False
        self.discord_user = await self.bot.getch_user(self.discord_id)
        if self.discord_user is None:
            return False
        self.user_db_data = await db_helper.get_player_data(
            self.bot, self.discord_id
        )
        if len(self.user_db_data) == 0:
            return False
        self.user_db_data = self.user_db_data[0]
        return True

    async def check_guild_channel(self):
        """checks if guild and channel are accessible and updates self"""
        guild_exists = self.bot.get_guild(self.guild)
        self.guild_data = await db_helper.get_guild_data(self.bot, self.guild)
        if guild_exists in self.bot.guilds and len(self.guild_data):
            # check if bot is still in the guild
            watch_channel_id = self.guild_data[0].get("watch_channel")
            channel_exists = self.bot.get_channel(watch_channel_id)
            guild_exists_channels = guild_exists.text_channels
            if channel_exists in guild_exists_channels:
                # check if channel is still in the guild
                self.channel = channel_exists
                self.channel_safe = True
                return

            # sends a warning that guild exists but channel is gone
            await db_helper.update_guild_data(
                self.bot, self.guild, watch_channel=0
            )
            if guild_exists_channels:
                await guild_exists_channels[0].send(
                    "The channel I am set to doesn't exist! Please set again."
                )
                return
        elif self.guild:
            # no longer have permission to DM user, just update guild data
            self.guild = 0
            await db_helper.update_player_data(
                self.bot, self.discord_id, guild_id=0
            )

    async def check_recent_is_newer(self, metadata):
        """checks if recent game is newer than stored last time"""
        start_time = metadata.get("game_start")  # given in s
        duration = metadata.get("game_length") / 1000  # given in ms
        self.recent_time = start_time + duration + 100
        user_data = await db_helper.get_player_data(self.bot, self.discord_id)
        if len(user_data) == 0:
            return False
        user_data = user_data[0]
        if user_data.get("lasttime") >= self.recent_time:
            return False
        return True

    def check__invalid_gamemode(self, mode):
        """returns True if gamemode is one of invalid modes"""
        invalid = ["Deathmatch"]
        return any(mode == x for x in invalid)

    async def retrieve_map_thumbnail(self, map_played):
        """retrieves the url of thumbnail for the map"""
        map_data = None
        map_request = await session.get(self.maps_url)
        if map_request.status != 200:
            return ""
        map_data = await map_request.json()
        for map_res in map_data.get("maps"):
            if map_res.get("name") == map_played:
                id = map_res.get("id")
                return f"https://media.valorant-api.com/maps/{id}/splash.png"
        return ""

    async def main(self):
        if not await self.check_current_user_exists():
            return

        self.puuid = self.user_db_data.get("puuid")
        self.region = self.user_db_data.get("region")
        self.guild = self.user_db_data.get("guild_id")
        self.channel = self.discord_user

        await self.check_guild_channel()

        match_request = await session.get(
            f"{self.matches_url}/{self.region}/{self.puuid}"
        )
        if match_request.status != 200:
            return
        match_data = await match_request.json()
        # loop through games
        for latest_game in match_data.get("data"):
            metadata = latest_game.get("metadata")
            if not metadata:
                continue
            if not await self.check_recent_is_newer(metadata):
                break
            mode = metadata.get("mode")
            if self.check__invalid_gamemode(mode):
                continue
            map_played = metadata.get("map")
            map_url = await self.retrieve_map_thumbnail(map_played)
            match_bg = ValorantMatchBackground(
                bot=self.bot,
                discord_id=self.discord_id,
                puuid=self.puuid,
                guild=self.guild,
                guild_data=self.guild_data,
                channel=self.channel,
                channel_safe=self.channel_safe,
                game=latest_game,
                recent_time=self.recent_time,
                mode=mode,
                map_played=map_played,
                map_url=map_url,
            )
            await match_bg.main()


class Background(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.valorant_watch_cycle = self.valorant_watch_cycle

    async def get_player_id_from_db(self):
        """retrieve player_ids from players db"""
        db_players = await self.bot.db.fetch("select player_id from players")
        return list(map(lambda x: x.get("player_id"), db_players))

    @tasks.loop()
    async def valorant_watch_cycle(self):
        await self.bot.wait_until_ready()  # wait until the bot logs in
        init_list = await self.get_player_id_from_db()
        for discord_id in init_list:
            valo_bg = ValorantBackground(bot=self.bot, discord_id=discord_id)
            await valo_bg.main()
            # sleeps for number of seconds (avoid rate limit)
            await asyncio.sleep(0.5)


def setup(bot: commands.Bot):
    bot.add_cog(Background(bot))
