"""classes for valorant watch"""

import os
import random
import re
from typing import Dict, List, Literal, Optional, Tuple, Union

import aiohttp
from disnake import Embed
from disnake.ext.commands import Bot

from helpers.db import GuildData, PlayerData, WaitlistData, db
from helpers.helpers import DiscordReturn

API = "https://api.henrikdev.xyz/valorant"
HEADERS = {"Authorization": os.environ.get("VALORANT_TOKEN")}


class Stats:
    """stats for valorant player

    attributes
    ----------
    streak: int
        current streak
    headshots: List[Optional[int]]
        number of headshots for each game or None if no headshots
    bodyshots: List[Optional[int]]
        number of bodyshots for each game or None if no bodyshots
    legshots: List[Optional[int]]
        number of legshots for each game or None if no legshots
    acs: List[Optional[float]]
        acs for each game or None if no acs
    kills: int
        kills in last game. used to check if player is feeding and is not
        saved in database
    deaths: int
        deaths in last game. used to check if player is feeding and is not
        saved in database
    assists: int
        assists in last game. used to check if player is feeding and is not
        saved in database
    prev_acs: float
        acs in last game. used to check if player is feeding and is not
        saved in database (only `acs` is saved in database)
    """

    def __init__(self) -> None:
        """initialises all stats to 0 or empty list"""
        self.streak: int = 0
        """current streak"""
        self.headshots: List[Optional[int]] = []
        """number of headshots for each game or None if no headshots"""
        self.bodyshots: List[Optional[int]] = []
        """number of bodyshots for each game or None if no bodyshots"""
        self.legshots: List[Optional[int]] = []
        """number of legshots for each game or None if no legshots"""
        self.acs: List[Optional[float]] = []
        """acs for each game or None if no acs"""
        self.kills: int = 0
        """kills in last game. used to check if player is feeding and is not
        saved in database"""
        self.deaths: int = 0
        """deaths in last game. used to check if player is feeding and is not
        saved in database"""
        self.assists: int = 0
        """assists in last game. used to check if player is feeding and is not
        saved in database"""
        self.prev_acs: float = 0
        """acs in last game. used to check if player is feeding and is not
        saved in database (only `acs` is saved in database)"""

    @staticmethod
    def sum_remove_none(
        _list: Union[List[Optional[int]], List[Optional[float]]]
    ) -> Union[int, float]:
        """returns sum of a list, removing None values

        parameters
        ----------
        _list: List[Union[int, float, None]]
            list to sum that may contain None values

        returns
        -------
        Union[int, float]
            sum of the list after removing None values
        """
        return sum(filter(None, _list))

    @staticmethod
    def is_feeding(deaths: int, kills: int) -> bool:
        """formula to check if player is feeding

        parameters
        ----------
        deaths: int
            number of deaths
        kills: int
            number of kills

        returns
        -------
        bool
            True if player is feeding, False otherwise
        """
        return deaths >= (kills + (1.1 * 2.71) ** (kills / 5) + 2.9)

    def check_feeding(self) -> bool:
        """checks if player is feeding based on last game stats

        returns
        -------
        bool
            True if player is feeding, False otherwise
        """
        return self.is_feeding(self.deaths, self.kills)

    def check_streaking(self) -> bool:
        """checks if player is on a streak (at least 3 games)

        returns
        -------
        bool
            True if player is on a streak, False otherwise
        """
        if abs(self.streak) >= 3:
            return True
        return False

    def num_games(self) -> int:
        """number of games saved

        returns
        -------
        int
            number of games saved
        """
        return len(self.headshots)

    def avg_headshots(self) -> float:
        """average fraction of total shots that are headshots

        returns
        -------
        float
            average headshot percentage
        """
        if self.num_games() == 0:
            return 0
        return self.sum_remove_none(self.headshots) / self.sum_remove_none(
            self.headshots + self.bodyshots + self.legshots
        )

    def avg_acs(self) -> float:
        """average acs of all saved games

        returns
        -------
        float
            average acs
        """
        if self.num_games() == 0:
            return 0
        return self.sum_remove_none(self.acs) / self.num_games()


class Match:
    """valorant match with metadata and players info

    attributes
    ----------
    mode: str
        the gamemode of the match
    map: str
        name of the map played
    game_end: int
        unix timestamp of when the match ended
    players: Dict[Literal["red", "blue"], List[Dict]]
        list of raw player info in the match, separated by team
    rounds_played: int
        number of rounds played in the match (excluding surrendered rounds)
    score: Dict[Literal["red", "blue"], int]
        score for each team
    surrender: bool
        True if match was surrendered, False otherwise
    red_win: Literal[1, -1, 0]
        1 if red won, -1 if blue won, 0 if draw
    map_thumbnail: str
        map thumbnail url if map name matches, empty string otherwise
    alert_embed: Embed
        creates an alert embed containing map thumbnail if any
    stats_embed: Embed
        creates a stats embed containing map thumbnail if any
    default_embeds: DiscordReturn
        creates a page view with an alert embed and a stats embed
    """

    def __init__(self, match_data: Dict) -> None:
        """initialises match with match data

        from match data, updates metadata (gamemode, map, game_end) and
        players (players, rounds_played, score, surrender)

        parameters
        ----------
        match_data: Dict
            match data from api

        raises
        ------
        ValueError
            if match data is None or metadata or players is None
        """
        if match_data is None:
            raise ValueError("match data is None!")
        metadata: Optional[Dict] = match_data.get("metadata")
        players: Optional[Dict[str, Dict]] = match_data.get("players")
        if metadata is None or players is None:
            raise ValueError("match data is None!")
        self.mode: str = ""
        """the gamemode of the match"""
        self.map: str = ""
        """name of the map played"""
        self.game_end: int = 0
        """unix timestamp of when the match ended"""
        self.players: Dict[Literal["red", "blue"], List[Dict]] = {
            "red": [],
            "blue": [],
        }
        """list of raw player info in the match, separated by team"""
        self.rounds_played: int = 0
        """number of rounds played in the match (excluding surrendered)"""
        self.score: Dict[Literal["red", "blue"], int] = {"red": 0, "blue": 0}
        """score for each team"""
        self.surrender: bool = False
        """True if match was surrendered, False otherwise"""
        self._map_thumbnail: str = ""

        self.update_metadata(metadata)
        if self.mode in ["Deathmatch", "Team Deathmatch"]:
            return
        self.players["red"] = players.get("red", [])
        self.players["blue"] = players.get("blue", [])
        rounds: Optional[List[Dict]] = match_data.get("rounds")
        if rounds is None:
            return
        self.update_rounds(rounds)

    @property
    def red_win(self) -> Literal[1, -1, 0]:
        """checks if red won, blue won, or draw from score

        returns
        -------
        Literal[1, -1, 0]
            1 if red won, -1 if blue won, 0 if draw
        """
        if self.score["red"] > self.score["blue"]:
            return 1
        if self.score["blue"] > self.score["red"]:
            return -1
        return 0

    @property
    async def map_thumbnail(self) -> str:
        """attempts to retrieve map thumbnail url from api by map name

        uses the `valorant-api` api to retrieve map info and checks if the
        map name matches the map name of the match. if it does, returns the
        map thumbnail url. otherwise, returns an empty string

        returns
        -------
        str
            map thumbnail url if map name matches, empty string otherwise
        """
        if self._map_thumbnail != "":
            return self._map_thumbnail
        async with aiohttp.ClientSession() as session:
            map_request: aiohttp.ClientResponse = await session.get(
                "https://valorant-api.com/v1/maps"
            )
            if map_request.status != 200:
                # raise ConnectionError("error retrieving map info!")
                return ""
            map_json: Dict[str, List] = await map_request.json()
        map_data: Optional[List[Dict]] = map_json.get("data")
        if map_data is None:
            # raise ConnectionError("error retrieving map info!")
            return ""
        for map_info in map_data:
            if map_info.get("displayName") == self.map:
                self._map_thumbnail = map_info.get("splash", "")
                return self._map_thumbnail
        return ""

    @property
    async def alert_embed(self) -> Embed:
        """creates an alert embed containing map thumbnail if any

        returns
        -------
        Embed
            alert embed containing map thumbnail if any
        """
        return Embed(
            title="valorant watch",
        ).set_thumbnail(await self.map_thumbnail)

    async def stats_embed(self, bot: Bot) -> Embed:
        """creates a stats embed containing map thumbnail if any

        parameters
        ----------
        bot: Bot
            bot instance
            bot instance is used to retrieve emojis

        returns
        -------
        Embed
            stats embed containing map thumbnail if any
        """
        stats_embed: Embed = Embed(
            title="match stats",
            description=f"🔴 **{self.score['red']} - {self.score['blue']}** 🔵",
            color=0x3737E1,
        ).set_thumbnail(await self.map_thumbnail)
        all_players_sorted: List[Dict] = sorted(
            self.players["red"] + self.players["blue"],
            key=lambda player: player.get("stats", {}).get("score", 0),
            reverse=True,
        )
        for player in all_players_sorted:
            team: Literal["🔴", "🔵"] = (
                "🔴" if player.get("team") == "Red" else "🔵"
            )
            stats: Dict = player.get("stats", {})
            kda: str = "/".join(
                [
                    str(stats.get("kills", 0)),
                    str(stats.get("deaths", 0)),
                    str(stats.get("assists", 0)),
                ]
            )
            acs: float = stats.get("score", 0) / self.rounds_played
            emojis: list = [
                emoji
                for emoji in bot.emojis
                if emoji.name
                == re.sub(r"[^a-zA-Z0-9]", "", player.get("character", ""))
            ]
            emoji: str = emojis[0] if len(emojis) > 0 else ""
            stats_embed.add_field(
                name=f"{team} {player.get('name')}#{player.get('tag')}",
                value=f"{emoji} {kda}  |  {int(acs)} ACS"
                + (
                    f"  |  {player.get('currenttier_patched', 'Unranked')}"
                    if self.mode == "Competitive"
                    else ""
                ),
                inline=False,
            )
        return stats_embed

    def check_mode(self) -> bool:
        """checks if match is competitive/unrated/custom game

        returns
        -------
        bool
            True if match is competitive/unrated/custom game, False otherwise
        """
        return self.mode in ("Competitive", "Unrated", "Custom Game")

    def update_metadata(self, metadata: Dict) -> None:
        """updates mode, map, and game_end from match data metadata

        parameters
        ----------
        metadata: Dict
            match data metadata
        """
        self.mode = metadata.get("mode", "")
        self.map = metadata.get("map", "")
        start: int = metadata.get("game_start", 0)
        length: int = metadata.get("game_length", 0)
        self.game_end = start + length

    def update_rounds(self, rounds: List[Dict]) -> None:
        """updates rounds_played, score, and surrender from match data rounds

        parameters
        ----------
        rounds: List[Dict]
            match data rounds
        """
        for _round in rounds:
            if _round.get("end_type") == "Surrendered":
                self.surrender = True
            else:
                self.rounds_played += 1
            self.score["red"] += _round.get("winning_team") == "Red"
            self.score["blue"] += _round.get("winning_team") == "Blue"

    def get_player_data(
        self, player: "Player"
    ) -> Optional[Tuple[Dict, Literal["red", "blue"]]]:
        """retreives player info from match data and the team they were on

        attempts to match the player's puuid with the match player's puuid

        parameters
        ----------
        player: Player
            player to retrieve info for

        returns
        -------
        Optional[Tuple[Dict, Literal["red", "blue"]]]
            tuple of player info and team they were on if found, None otherwise
        """
        for team in ("red", "blue"):
            for match_player in self.players[team]:
                if match_player.get("puuid") == player.puuid:
                    return match_player, team
        return None

    def check_players(
        self, main_player: "Player", all_players: List["Player"]
    ) -> Tuple[List["Player"], List["Player"]]:
        """checks and returns players in the match who are in the same guild
        as the main player

        parameters
        ----------
        main_player: Player
            player to check against
        all_players: List[Player]
            list of all players to check

        returns
        -------
        Tuple[List[Player], List[Player]]
            tuple of red players and blue players in the same guild as the main
            player
        """
        main_guild_id: int = main_player.guild_id
        all_puuids_with_guild: Dict[str, "Player"] = {
            player.puuid: player for player in all_players
        }
        red_players: List["Player"] = []
        blue_players: List["Player"] = []
        for match_player in self.players["red"]:
            puuid: str = match_player.get("puuid", "")
            player: Optional[Player] = all_puuids_with_guild.get(puuid)
            if player is None or player.guild_id != main_guild_id:
                continue
            red_players.append(player)
        for match_player in self.players["blue"]:
            puuid: str = match_player.get("puuid", "")
            player: Optional[Player] = all_puuids_with_guild.get(puuid)
            if player is None or player.guild_id != main_guild_id:
                continue
            blue_players.append(player)
        return red_players, blue_players

    def add_players_to_embed(
        self,
        embed: Embed,
        red_players: List["Player"],
        blue_players: List["Player"],
    ) -> None:
        """adds players info to embed description

        parameters
        ----------
        embed: Embed
            embed to add players info to
        red_players: List[Player]
            list of red players to add
        blue_players: List[Player]
            list of blue players to add
        """
        if len(red_players) == 0 and len(blue_players) == 0:
            return
        desc: str = ""
        red_players_str: str = "and ".join(
            [f"<@{player.player_id}>" for player in red_players]
        )
        blue_players_str: str = "and ".join(
            [f"<@{player.player_id}>" for player in blue_players]
        )
        action: dict[int, str] = {
            1: f"just wonnered a {self.mode} game",
            -1: f"just losted a {self.mode} game",
            0: f"just finished a {self.mode} game",
        }
        color: dict[int, int] = {1: 0x17DC33, -1: 0xDC3317, 0: 0x767676}
        if len(red_players) > 0:
            desc += red_players_str + " "  # mention red players
            desc += action[self.red_win] + " "  # won/lost/draw
            desc += f"__**{self.score['red']} - {self.score['blue']}**__ "
            if self.surrender:
                desc += "(surrender) "
            desc += f"on **{self.map} **"  # map played
            desc += f"<t:{int(self.game_end)}:R>!"  # timestamp
            embed.color = color[self.red_win]  # set color
            if len(blue_players) > 0:  # both teams
                desc += "\n" + blue_players_str + " "
                desc += "played on the other team!"
                embed.color = color[0]
        else:
            desc += blue_players_str + " "  # mention blue players
            desc += action[-self.red_win] + " "  # won/lost/draw
            desc += f"__**{self.score['blue']} - {self.score['red']}**__ "
            if self.surrender:
                desc += "(surrender) "
            desc += f"on **{self.map} **"  # map played
            desc += f"<t:{int(self.game_end)}:R>!"  # timestamp
            embed.color = color[-self.red_win]  # set color
        embed.description = desc
        return

    async def add_feeders_to_embed(
        self, embed: Embed, feeders: List["Player"]
    ) -> None:
        """adds feeders info to embed fields if any

        retrieves guild's custom messages and images if set and selects a
        random message and image to add to the embed

        parameters
        ----------
        embed: Embed
            embed to add feeders info to
        feeders: List[Player]
            list of feeders to add
        """
        if len(feeders) == 0:
            return
        # default messages and images
        messages: List[str] = ["lmao", "git gud"]
        images: List[str] = [
            "https://i.ytimg.com/vi/PZe1FbclgpM/maxresdefault.jpg"
        ]
        # retrieve guild's custom if set
        guild_id: int = feeders[0].guild_id
        guild_data: List[GuildData] = await db.get_guild_data(guild_id)
        if len(guild_data) > 0:
            messages = guild_data[0]["feeder_messages"] or messages
            images = guild_data[0]["feeder_images"] or images
        # add feeders to embed
        embed.add_field(
            name=f"feeder alert❗❗ {random.choice(messages)}",
            value="\n".join(
                [
                    f"<@{feeder.player_id}> finished"
                    + f" {feeder.kills}/{feeder.deaths}/{feeder.assists}"
                    + f" with an ACS of {int(feeder.prev_acs)}"
                    for feeder in feeders
                ]
            ),
            inline=False,
        ).set_image(url=random.choice(images))

    async def add_streakers_to_embed(
        self, embed: Embed, streakers: List["Player"]
    ) -> None:
        """adds streakers info to embed fields if any

        retrieves guild's custom messages if set and selects a random message
        to add to the embed

        parameters
        ----------
        embed: Embed
            embed to add streakers info to
        streakers: List[Player]
            list of streakers to add
        """
        if len(streakers) == 0:
            return
        # default messages
        messages: list[str] = ["wow streak", "damn"]
        # retrieve guild's custom if set
        guild_id: int = streakers[0].guild_id
        guild_data: List[GuildData] = await db.get_guild_data(guild_id)
        if len(guild_data) > 0:
            messages = guild_data[0]["streaker_messages"] or messages
        # add streakers to embed
        embed.add_field(
            name=f"streaker alert 👀👀 {random.choice(messages)}",
            value="\n".join(
                [
                    f"<@{streaker.player_id}> is on a"
                    + f" {abs(streaker.streak)}-game"
                    + f" {'winning' if streaker.streak > 0 else 'losing'}"
                    + " streak!"
                    for streaker in streakers
                ]
            ),
            inline=False,
        )

    def waiters_to_content(self, waiters: List[int]) -> str:
        """joins waiters into a string to be sent as content

        parameters
        ----------
        waiters: List[int]
            list of waiters discord id to join
        """
        if len(waiters) == 0:
            return ""
        _waiters = map(str, (set(waiters)))
        return f"removing <@{'> and <@'.join(_waiters)}> from waitlist!"

    async def trigger_alert(
        self, main_player: "Player", all_players: List["Player"]
    ) -> Optional[DiscordReturn]:
        """trigger the valorant watch alert and
        return an embed with content if any

        updates all players' stats and checks for feeders and streakers
        and removes waiters from waitlist

        parameters
        ----------
        main_player: Player
            player to check against
        all_players: List[Player]
            list of all players to check

        returns
        -------
        Optional[DiscordReturn]
            embed with content if any
        """
        alert_embed: Embed = await self.alert_embed
        red_players: List["Player"]
        blue_players: List["Player"]
        red_players, blue_players = self.check_players(
            main_player, all_players
        )
        if len(red_players) == 0 and len(blue_players) == 0:
            return
        feeders: list["Player"] = []
        streakers: list["Player"] = []
        waiters: list[int] = []
        for player in red_players + blue_players:
            player.process_match(self)
            await player.update_db()
            waitlist_data: List[WaitlistData]
            waitlist_data = await db.get_waitlist_data(player.player_id)
            if len(waitlist_data) > 0:
                _waiters: Optional[List[int]] = waitlist_data[0]["waiting_id"]
                if _waiters is not None:
                    waiters += _waiters
                await db.delete_waitlist_data(player.player_id)
            if not self.check_mode():
                continue
            if player.check_feeding():
                feeders.append(player)
            if self.game_end >= player.lasttime and player.check_streaking():
                streakers.append(player)
        if not self.check_mode():
            return
        self.add_players_to_embed(alert_embed, red_players, blue_players)
        await self.add_feeders_to_embed(alert_embed, feeders)
        await self.add_streakers_to_embed(alert_embed, streakers)
        return {
            "content": self.waiters_to_content(waiters),
            "embed": alert_embed,
        }


class Player(Stats):
    """valorant player with stats and account info

    attributes
    ----------
    player_id: int
        discord id of the player
    guild_id: int
        discord id of the guild the player is in
    name: str
        valorant username of the player
    tag: str
        valorant tag of the player
    region: str
        valorant region of the player
    puuid: str
        valorant puuid of the player
    lasttime: int
        unix timestamp of when the player last played a match
    card: str
        valorant card id of the player
    rank: str
        valorant rank of the player
    """

    def __init__(
        self, *datas: Union[Dict, PlayerData], **kwargs: Dict
    ) -> None:
        """initialises player with player data

        multiple datas can be passed in to set the attributes of the player.
        kwargs can also be passed in to set the attributes of the player.

        parameters
        ----------
        datas: Union[Dict, PlayerData]
            player data from database
        kwargs: Dict
            player data from api
        """
        super().__init__()
        self.player_id: int = 0
        """discord id of the player"""
        self.guild_id: int = 0
        """discord id of the guild the player is in"""
        self.name: str = ""
        """valorant username of the player"""
        self.tag: str = ""
        """valorant tag of the player"""
        self.region: str = ""
        """valorant region of the player"""
        self.puuid: str = ""
        """valorant puuid of the player"""
        self.lasttime: int = 0
        """unix timestamp of when the player last played a match"""
        self.card: str = ""
        """valorant card id of the player"""
        self.rank: str = ""
        """valorant rank of the player"""
        for data in datas:
            for key, value in data.items():
                setattr(self, key, value)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self) -> str:
        return f"{self.name}#{self.tag}"

    def __repr__(self) -> str:
        return f"{self.name}#{self.tag}"

    async def update_puuid_region(self) -> None:
        """updates puuid and region from api from name and tag

        raises
        ------
        ConnectionError
            if error retrieving account info
        """
        async with aiohttp.ClientSession() as session:
            account_request: aiohttp.ClientResponse = await session.get(
                f"{API}/v1/account/{self.name}/{self.tag}",
                headers=HEADERS,
            )
            if account_request.status != 200:
                raise ConnectionError("error retrieving account info!")
            account_json: Dict[str, Dict] = await account_request.json()
        account_data: Optional[Dict] = account_json.get("data")
        if account_data is None:
            raise ConnectionError("error retrieving account info!")
        self.puuid = account_data.get("puuid") or self.puuid
        self.region = account_data.get("region") or self.region
        self.card = account_data.get("card", {}).get("id") or self.card

    async def update_name_tag(self) -> None:
        """updates name tag and region from api from puuid

        non-critical and if error, name and tag are not updated
        """
        async with aiohttp.ClientSession() as session:
            account_request: aiohttp.ClientResponse = await session.get(
                f"{API}/v1/by-puuid/account/{self.puuid}",
                headers=HEADERS,
            )
            if account_request.status != 200:
                # raise ConnectionError("error retrieving account info!")
                return
            account_json: Dict[str, Dict] = await account_request.json()
        account_data: Optional[Dict] = account_json.get("data")
        if account_data is None:
            # raise ConnectionError("error retrieving account info!")
            return
        name: Optional[str] = account_data.get("name")
        tag: Optional[str] = account_data.get("tag")
        region: Optional[str] = account_data.get("region")
        if name is None or tag is None:
            # raise ConnectionError("error retrieving account info!")
            return
        self.name = name
        self.tag = tag
        self.region = region or self.region
        self.card = account_data.get("card", {}).get("id") or self.card

    async def get_match_history(self) -> List[Match]:
        """retrieve match history from api

        returns
        -------
        List[Match]
            list of matches from oldest to newest

        raises
        ------
        ConnectionError
            if error retrieving match history
        """
        async with aiohttp.ClientSession() as session:
            match_request: aiohttp.ClientResponse = await session.get(
                f"{API}/v3/by-puuid/matches/{self.region}/{self.puuid}",
                headers=HEADERS,
            )
            if match_request.status != 200:
                raise ConnectionError("error retrieving match history!")
            match_json: Dict[str, List] = await match_request.json()
        match_data: Optional[List[Dict]] = match_json.get("data")
        if match_data is None:
            raise ConnectionError("error retrieving match history!")
        matches: List[Match] = []
        for match in match_data:
            try:
                matches.append(Match(match))
            except ValueError:
                continue
        return matches[::-1]

    def process_match(self, match: Match) -> None:
        """process match information and updates player stats and information

        skips match if match is not Unrated/Competitive/Custom Game, or if
        player is not in the match.
        sets kills, deaths, assists and prev_acs to the player's stats in the
        match. actual stats are only updated if match is competitive/unrated
        and game_end is after lasttime.

        parameters
        ----------
        match: Match
            match to process
        """
        # only add stats for competitive/unrated/custom games
        if self.lasttime >= match.game_end:
            return
        self.lasttime = match.game_end
        if not match.check_mode():
            return
        check: Optional[Tuple[Dict, Literal["red", "blue"]]] = (
            match.get_player_data(self)
        )
        if check is None:
            return
        player: Dict
        team: Literal["red", "blue"]
        player, team = check
        player_stats: Optional[Dict] = player.get("stats")
        if player_stats is None:
            return
        self.kills = player_stats.get("kills")
        self.deaths = player_stats.get("deaths")
        self.assists = player_stats.get("assists")
        self.prev_acs = player_stats.get("score") / match.rounds_played
        # update streak
        if match.red_win == 0:
            pass
        elif (team == "red") ^ (match.red_win == 1):
            self.streak = min(self.streak - 1, -1)
        else:
            self.streak = max(self.streak + 1, 1)
        if match.mode == "Competitive":
            self.rank = player.get("currenttier_patched", self.rank)
        self.update_stats(
            self.prev_acs,
            player_stats.get("headshots"),
            player_stats.get("bodyshots"),
            player_stats.get("legshots"),
        )

    def update_stats(
        self, acs: float, headshots: int, bodyshots: int, legshots: int
    ) -> None:
        """updates player stats with new stats

        each stat is limited to the last 5 games

        parameters
        ----------
        acs: float
            acs of the game
        headshots: int
            number of headshots in the game
        bodyshots: int
            number of bodyshots in the game
        legshots: int
            number of legshots in the game
        """
        self.acs = self.acs[-4:] + [acs]
        self.headshots = self.headshots[-4:] + [headshots]
        self.bodyshots = self.bodyshots[-4:] + [bodyshots]
        self.legshots = self.legshots[-4:] + [legshots]

    def process_matches(self, matches: List[Match]) -> None:
        """process list of matches and updates player stats and information"""
        for match in matches:
            self.process_match(match)

    async def update_db(self) -> str:
        """updates player data in database"""
        return await db.update_player_data(
            self.player_id,
            guild_id=self.guild_id,
            name=self.name,
            tag=self.tag,
            region=self.region,
            puuid=self.puuid,
            lasttime=self.lasttime,
            streak=self.streak,
            headshots=self.headshots,
            bodyshots=self.bodyshots,
            legshots=self.legshots,
            acs=self.acs,
            rank=self.rank,
        )

    def info_embed(self) -> Embed:
        """returns embed containing player info and stats

        returns
        -------
        Embed
            embed containing player info and stats
        """
        embed: Embed = (
            Embed(
                title="valorant info",
                description=f"<@{self.player_id}> saved info",
                color=0x3737E1,
            )
            .add_field(
                name="username",
                value=f"{self.name}#{self.tag}",
            )
            .add_field(
                name="last updated",
                value=f"<t:{int(self.lasttime)}>",
            )
            .set_image(
                url=f"https://media.valorant-api.com/playercards/{self.card}"
                + "/wideart.png"
            )
        )
        if self.rank:
            embed.add_field(
                name="",
                value="",
                inline=False,
            )
            embed.add_field(
                name="rank",
                value=self.rank,
            )
        if self.streak:
            embed.add_field(
                name="streak",
                value=f"{abs(self.streak)}-game "
                + ("winning " if self.streak > 0 else "losing ")
                + "streak",
            )
        if self.num_games():
            embed.add_field(
                name="",
                value="",
                inline=False,
            )
            embed.add_field(
                name="headshot %",
                value=f"{self.avg_headshots():.0%}",
            ).add_field(
                name="ACS",
                value=int(self.avg_acs()),
            ).set_footer(
                text=f"from last {self.num_games()} ranked/unrated games"
            )
        return embed
