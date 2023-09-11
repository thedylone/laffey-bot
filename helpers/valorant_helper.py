"""helper functions for valorant cog"""

import aiohttp
from typing import Dict, List, Literal, Tuple, Optional, Union
from disnake import (
    ApplicationCommandInteraction,
    Embed,
    File,
    Guild,
    Member,
    ModalInteraction,
    Role,
    TextChannel,
    Thread,
    User,
    VoiceChannel,
    channel,
)
from disnake.ext import commands

from helpers.db_helper import db
from helpers.helpers import DiscordReturn, validate_url
from views.views import DeleterView, Menu

API = "https://api.henrikdev.xyz/valorant"


class Stats:
    """class for valorant stats"""

    def __init__(self) -> None:
        self.streak: int = 0
        self.headshots: List[Union[int, None]] = []
        self.bodyshots: List[Union[int, None]] = []
        self.legshots: List[Union[int, None]] = []
        self.acs: List[Union[float, None]] = []

    @staticmethod
    def sum_remove_none(_list: List) -> Union[int, float]:
        """returns sum of list, removing None"""
        return sum(filter(None, _list))

    def num_games(self) -> int:
        """returns number of games"""
        return len(self.headshots)

    def avg_headshots(self) -> float:
        """returns average headshots"""
        if self.num_games() == 0:
            return 0
        return self.sum_remove_none(self.headshots) / self.sum_remove_none(
            self.headshots + self.bodyshots + self.legshots
        )

    def avg_acs(self) -> float:
        """returns average acs"""
        if self.num_games() == 0:
            return 0
        return self.sum_remove_none(self.acs) / self.num_games()


class Match:
    """class for valorant match"""

    mode: str = ""
    map: str = ""
    game_end: int = 0
    players: Dict[str, List[Dict]] = {"red": [], "blue": []}
    rounds_played: int = 0
    score: Dict[str, int] = {"red": 0, "blue": 0}
    surrender: bool = False

    def __init__(self, match_data: Dict) -> None:
        if match_data is None:
            return
        metadata: Optional[Dict] = match_data.get("metadata")
        players: Optional[Dict[str, Dict]] = match_data.get("players")
        if metadata is None or players is None:
            return
        self.update_metadata(metadata)
        if self.mode == "Deathmatch":
            return
        self.players["red"] = players.get("red", [])
        self.players["blue"] = players.get("blue", [])
        rounds: Optional[List[Dict]] = match_data.get("rounds")
        if rounds is None:
            return
        self.update_rounds(rounds)

    def update_metadata(self, metadata: Dict) -> None:
        """update metadata from match data"""
        self.mode = metadata.get("mode", "")
        self.map = metadata.get("map", "")
        start: int = metadata.get("game_start", 0)
        length: int = metadata.get("game_length", 0)
        self.game_end = start + length

    def update_rounds(self, rounds: List[Dict]) -> None:
        """update rounds from match data"""
        for _round in rounds:
            if _round.get("end_type") == "Surrendered":
                self.is_surrendered = True
            else:
                self.rounds_played += 1
            self.score["red"] += _round.get("winning_team") == "Red"
            self.score["blue"] += _round.get("winning_team") == "Blue"

    def check_players(
        self, main_player: "Player", all_players: List["Player"]
    ) -> Tuple[List[Dict], List[Dict], Literal["red", "blue", ""]]:
        """check players in match, returns red, blue, main_team"""
        main_puuid: str = main_player.puuid
        main_guild_id: int = main_player.guild_id
        all_puuids_with_guild: Dict[str, "Player"] = {
            player.puuid: player for player in all_players
        }
        red_players: List[Dict] = []
        blue_players: List[Dict] = []
        main_team: str = ""
        for match_player in self.players["red"]:
            puuid: str = match_player.get("puuid", "")
            player: Optional[Player] = all_puuids_with_guild.get(puuid)
            if puuid == main_puuid:
                main_team = "red"
            elif player is None or player.guild_id != main_guild_id:
                continue
            red_players.append(match_player)
        for match_player in self.players["blue"]:
            puuid: str = match_player.get("puuid", "")
            player: Optional[Player] = all_puuids_with_guild.get(puuid)
            if puuid == main_puuid:
                main_team = "blue"
            elif player is None or player.guild_id != main_guild_id:
                continue
            blue_players.append(match_player)
        return red_players, blue_players, main_team


class Player(Stats):
    """class for valorant player"""

    player_id: int = 0
    guild_id: int = 0
    name: str = ""
    tag: str = ""
    region: str = ""
    puuid: str = ""
    lasttime: int = 0

    def __init__(self, *datas: Dict, **kwargs: Dict) -> None:
        super().__init__()
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
        """get account info from api. updates puuid and region"""
        async with aiohttp.ClientSession() as session:
            account_request: aiohttp.ClientResponse = await session.get(
                f"{API}/v1/account/{self.name}/{self.tag}"
            )
            if account_request.status != 200:
                raise ConnectionError("error retrieving account info!")
            account_json: Dict[str, Dict] = await account_request.json()
        account_data: Optional[Dict] = account_json.get("data")
        if account_data is None:
            raise ConnectionError("error retrieving account info!")
        self.puuid = account_data.get("puuid") or self.puuid
        self.region = account_data.get("region") or self.region

    async def update_name_tag(self) -> None:
        """get account info from api. updates name and tag"""
        async with aiohttp.ClientSession() as session:
            account_request: aiohttp.ClientResponse = await session.get(
                f"{API}/v1/by-puuid/account/{self.puuid}"
            )
            if account_request.status != 200:
                raise ConnectionError("error retrieving account info!")
            account_json: Dict[str, Dict] = await account_request.json()
        account_data: Optional[Dict] = account_json.get("data")
        if account_data is None:
            raise ConnectionError("error retrieving account info!")
        name: Optional[str] = account_data.get("name")
        tag: Optional[str] = account_data.get("tag")
        if name is None or tag is None:
            raise ConnectionError("error retrieving account info!")
        self.name = name
        self.tag = tag

    async def get_match_history(self) -> List[Match]:
        """returns list of matches from oldest to newest"""
        async with aiohttp.ClientSession() as session:
            match_request: aiohttp.ClientResponse = await session.get(
                f"{API}/v3/by-puuid/matches/{self.region}/{self.puuid}"
            )
            if match_request.status != 200:
                raise ConnectionError("error retrieving match history!")
            match_json: Dict[str, List] = await match_request.json()
        match_data: Optional[List[Dict]] = match_json.get("data")
        if match_data is None:
            raise ConnectionError("error retrieving match history!")
        return [Match(data) for data in match_data][::-1]

    def process_match(self, match: Match) -> None:
        """process match information and updates player"""
        # update lasttime
        if self.lasttime >= match.game_end:
            return
        if match.mode == "Deathmatch":
            return
        red: List[Dict]
        blue: List[Dict]
        team: str
        red, blue, team = match.check_players(self, [])
        combined = red + blue
        if len(combined) == 0:
            return
        # update streak
        if team == "Red" and (match.score["red"] > match.score["blue"]):
            self.streak = max(self.streak + 1, 1)
        elif team == "Blue" and (match.score["blue"] > match.score["red"]):
            self.streak = min(self.streak - 1, -1)
        # only add stats for competitive/unrated
        if match.mode not in ("Competitive", "Unrated"):
            return
        player_stats: Optional[Dict] = combined[0].get("stats")
        if player_stats is None:
            return
        self.update_stats(
            player_stats.get("score") / match.rounds_played,
            player_stats.get("headshots"),
            player_stats.get("bodyshots"),
            player_stats.get("legshots"),
        )

    # def process_match_stats(self, stats: Dict) -> None:

    def update_stats(
        self, acs: float, headshots: int, bodyshots: int, legshots: int
    ) -> None:
        """updates player stats"""
        self.acs = self.acs[-4:] + [acs]
        self.headshots = self.headshots[-4:] + [headshots]
        self.bodyshots = self.bodyshots[-4:] + [bodyshots]
        self.legshots = self.legshots[-4:] + [legshots]

    def process_matches(self, matches: List[Match]) -> None:
        """process list of matches and updates player"""
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
        )

    def info_embed(self) -> Embed:
        """returns embed with player info"""
        embed: Embed = (
            Embed(
                title="valorant info",
                description=f"<@{self.player_id}> saved info",
            )
            .add_field(
                name="username",
                value=f"{self.name}#{self.tag}",
                inline=True,
            )
            .add_field(
                name="last updated",
                value=f"<t:{int(self.lasttime)}>",
                inline=True,
            )
        )
        if self.num_games():
            embed.add_field(
                name="headshot %",
                value=f"{self.avg_headshots():.0%}",
                inline=False,
            ).add_field(
                name="ACS",
                value=int(self.avg_acs()),
                inline=True,
            ).set_footer(
                text=f"from last {self.num_games()} ranked/unrated games"
            )
        return embed


def use_prefix(
    message: Union[
        ApplicationCommandInteraction, commands.Context, ModalInteraction
    ],
) -> Optional[str]:
    """returns the prefix to use depending on message"""
    if isinstance(message, commands.Context):
        return message.prefix
    return "/"


async def ping(
    message: Union[ApplicationCommandInteraction, commands.Context],
) -> DiscordReturn:
    """pings role and sends optional image."""
    if message.guild is None:
        guild_id = 0
    else:
        guild_id: int = message.guild.id
    guild_data: List = await db.get_guild_data(guild_id)
    if len(guild_data) == 0 or not guild_data[0].get("ping_role"):
        prefix: Optional[str] = use_prefix(message)
        return {
            "content": f"please set the role first using {prefix}set-role!",
        }
    ping_role: int = guild_data[0].get("ping_role")
    if guild_data[0].get("ping_image"):
        url: str = guild_data[0].get("ping_image")
        embed: Embed = Embed().set_image(url=url)
        return {"content": f"<@&{ping_role}>", "embed": embed}
    return {"content": f"<@&{ping_role}>", "file": File("jewelsignal.jpg")}


async def ping_image_add(
    message: Union[
        ApplicationCommandInteraction, commands.Context, ModalInteraction
    ],
    new_image: str,
) -> DiscordReturn:
    """add custom image for ping."""
    if len(new_image) > 100:
        return {"content": "url is too long! (max 100 characters)"}
    if not validate_url(new_image):
        return {"content": "invalid url!"}
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    result: str = await db.update_guild_data(guild.id, ping_image=new_image)
    if result.startswith("INSERT"):
        content: str = f"successfully added custom ping image for `{guild}`"
    elif result.startswith("UPDATE"):
        content = f"successfully updated custom ping image for `{guild}`"
    else:
        content = f"error updating custom ping image for `{guild}`"
    return {"content": content}


async def ping_image_show(
    message: Union[ApplicationCommandInteraction, commands.Context],
) -> DiscordReturn:
    """show custom image for ping."""
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    guild_data: List = await db.get_guild_data(guild.id)
    if len(guild_data) == 0 or not guild_data[0].get("ping_image"):
        use_msg: str = (
            f'use {use_prefix(message)}ping-image add "<custom image>"!'
        )
        return {"content": f"no custom image for `{guild}`! {use_msg}"}
    ping_image: str = guild_data[0].get("ping_image")
    embed = Embed(
        title="custom ping image",
        description="image sent with the ping",
    )
    embed.set_image(url=ping_image)
    return {"embed": embed}


async def ping_image_delete(
    message: Union[ApplicationCommandInteraction, commands.Context],
) -> DiscordReturn:
    """delete custom image for ping"""
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    result: str = await db.update_guild_data(guild.id, ping_image=None)
    if result.startswith("INSERT"):
        content: str = f"successfully deleted custom ping image for `{guild}`"
    elif result.startswith("UPDATE"):
        content = f"successfully deleted custom ping image for `{guild}`"
    else:
        content = f"error deleting custom ping image for `{guild}`"
    return {"content": content}


async def info(
    message: Union[ApplicationCommandInteraction, commands.Context],
    user: Optional[Union[User, Member]] = None,
) -> DiscordReturn:
    """returns user's valorant info from the database."""
    if user is None:
        # if no user specifieembedd, use author
        user = message.author
    player_data: List = await db.get_player_data(user.id)
    if len(player_data) == 0:
        use_msg: str = f"use {use_prefix(message)}valorant-watch first!"
        return {"content": f"<@{user.id}> user not in database. {use_msg}"}

    player: Player = Player(player_data[0])
    # create embed
    return {
        "embed": player.info_embed().set_thumbnail(url=user.display_avatar.url)
    }


async def watch(
    message: Union[
        ApplicationCommandInteraction, commands.Context, ModalInteraction
    ],
    name: str,
    tag: str,
) -> DiscordReturn:
    """add user's valorant info to the database."""
    guild_id: int = 0
    if not isinstance(message.channel, channel.DMChannel) and message.guild:
        guild_id = message.guild.id
        guild_data: List = await db.get_guild_data(guild_id)
        if len(guild_data) == 0 or not guild_data[0].get("watch_channel"):
            use_msg: str = f"use {use_prefix(message)}set-channel first!"
            return {"content": f"<@{message.author.id}> {use_msg}"}

    tag = tag.replace("#", "")
    user_id: int = message.author.id
    player: Player = Player(
        {"player_id": user_id, "guild_id": guild_id, "name": name, "tag": tag},
    )
    await player.update_puuid_region()
    player.process_matches(await player.get_match_history())
    result: str = await player.update_db()
    if result.startswith("INSERT"):
        content: str = f"<@{user_id}> user added to database."
    elif result.startswith("UPDATE"):
        content = f"<@{user_id}> user updated in database."
    else:
        content = f"<@{user_id}> error updating, user not in database"
    return {"content": content}


async def unwatch(
    message: Union[ApplicationCommandInteraction, commands.Context],
) -> DiscordReturn:
    """removes user's valorant info from the database."""
    user_id: int = message.author.id
    user_data: List = await db.get_player_data(user_id)
    if len(user_data):
        await db.delete_player_data(user_id)
        use_msg: str = f"add again using {use_prefix(message)}valorant-watch!"
        content: str = f"<@{user_id}> user removed from database. {use_msg}"
    else:
        content = f"<@{user_id}> error updating, user not in database"
    return {"content": content}


async def wait(
    message: Union[ApplicationCommandInteraction, commands.Context],
    *wait_users: User,
) -> DiscordReturn:
    """pings you when tagged user(s) is/are done."""
    message_user_id: int = message.author.id
    if len(wait_users) == 0:
        use_msg: str = f"use {use_prefix(message)}valorant-wait <tag the user>"
        return {"content": f"<@{message_user_id}> {use_msg}"}
    extra_message: str = ""
    success_waiting: List[int] = []
    already_waited: List[int] = []
    non_db: List[int] = []
    for wait_user_id in map(lambda user: user.id, wait_users):
        if wait_user_id == message_user_id:
            # if wait for self
            extra_message = "interesting but ok."
        # retrieve waitlist and player info
        player_data: List = await db.get_players_join_waitlist(wait_user_id)
        if len(player_data):
            current_waiters: List = player_data[0].get("waiting_id")
            if current_waiters:
                if message_user_id in current_waiters:
                    already_waited.append(wait_user_id)
                    continue
            else:
                current_waiters = []
            await db.update_waitlist_data(
                wait_user_id, current_waiters + [message_user_id]
            )
            success_waiting.append(wait_user_id)
        else:
            non_db.append(wait_user_id)
    success_message: str = (
        f"you're now waiting for <@{'> <@'.join(map(str, success_waiting))}>."
        if success_waiting
        else ""
    )
    already_message: str = (
        f"you're still waiting for <@{'> <@'.join(map(str, already_waited))}>."
        if already_waited
        else ""
    )
    non_db_message: str = (
        f"<@{'> <@'.join(map(str, non_db))}> not in database, unable to wait."
        if non_db
        else ""
    )
    return {
        "content": " ".join(
            filter(
                None,
                [
                    extra_message,
                    f"<@{message_user_id}>",
                    success_message,
                    already_message,
                    non_db_message,
                ],
            )
        )
    }


async def waitlist(
    message: Union[ApplicationCommandInteraction, commands.Context],
) -> DiscordReturn:
    """prints valorant waitlist."""
    guild_id: int = 0
    if not isinstance(message.channel, channel.DMChannel) and message.guild:
        guild_id = message.guild.id
    # create embed
    embed = Embed(
        title="valorant waitlist", description="waitlist of watched users"
    )
    embed.set_thumbnail(url="https://i.redd.it/pxwk9pc6q9n91.jpg")
    waitlist_data: List = await db.get_waitlist_join_players()
    for player in waitlist_data:
        player_id: int = player.get("player_id")
        if guild_id == 0 and message.author.id in player.get("waiting_id"):
            # not sent to guild, show all players the user is waiting for
            embed.add_field(name="user", value=f"<@{player_id}>", inline=False)
            embed.add_field(name="waiters", value=f"<@{message.author.id}>")
        elif (
            player_id == message.author.id
            or guild_id
            and player.get("guild_id") == guild_id
        ):
            # sent to guild, show all waiters for user who set in current guild
            embed.add_field(name="user", value=f"<@{player_id}>", inline=False)
            embed.add_field(
                name="waiters",
                value=f"<@{'> <@'.join(map(str, player.get('waiting_id')))}>",
            )
    return {"embed": embed}


async def set_channel(
    message: Union[ApplicationCommandInteraction, commands.Context],
    _channel: Optional[Union[TextChannel, VoiceChannel, Thread]] = None,
) -> DiscordReturn:
    """set the channel the bot will send updates to."""
    if _channel is None:
        channel_id: int = message.channel.id
    else:
        channel_id = _channel.id
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    result: str = await db.update_guild_data(
        guild.id, watch_channel=channel_id
    )
    if result.startswith("INSERT"):
        content: str = (
            f"successfully set channel <#{channel_id}> for `{guild}`"
        )
    elif result.startswith("UPDATE"):
        content = f"successfully updated channel <#{channel_id}> for `{guild}`"
    else:
        content = f"error updating channel for `{guild}`"
    return {"content": content}


async def set_role(
    message: Union[ApplicationCommandInteraction, commands.Context],
    role: Optional[Role] = None,
) -> DiscordReturn:
    """set the role to ping."""
    if role is None:
        return {"content": f"use {use_prefix(message)}set-role <role>!"}
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    result: str = await db.update_guild_data(guild.id, ping_role=role.id)
    if result.startswith("INSERT"):
        content: str = f"successfully set role `{role}` for `{guild}`"
    elif result.startswith("UPDATE"):
        content = f"successfully updated role `{role}` for `{guild}`"
    else:
        content = f"error updating role for `{guild}`"
    return {"content": content}


async def feeder_message_add(
    message: Union[
        ApplicationCommandInteraction, commands.Context, ModalInteraction
    ],
    new_message: str,
) -> DiscordReturn:
    """add custom message for feeder alert."""
    if len(new_message) > 100:
        return {"content": "message is too long! (max 100 characters)"}
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    guild_data: List = await db.get_guild_data(guild.id)
    if len(guild_data) == 0:
        return {"content": f"error! `{guild}` not in database"}
    feeder_messages: Optional[List] = guild_data[0].get("feeder_messages")
    if feeder_messages and len(feeder_messages) >= 25:
        return {
            "content": "max number reached! delete before adding a new one!"
        }
    if feeder_messages:
        feeder_messages.append(new_message)
    else:
        feeder_messages = [new_message]
    result: str = await db.update_guild_data(
        guild.id, feeder_messages=feeder_messages
    )
    if result.startswith("INSERT"):
        content: str = (
            f"successfully added custom feeder message for `{guild}`"
        )
    elif result.startswith("UPDATE"):
        content = f"successfully updated custom feeder message for `{guild}`"
    else:
        content = f"error updating custom feeder message for `{guild}`"
    return {"content": content}


async def feeder_message_show(
    message: Union[ApplicationCommandInteraction, commands.Context],
) -> DiscordReturn:
    """show custom messages for feeder alert."""
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    guild_data: List = await db.get_guild_data(guild.id)
    if len(guild_data) == 0:
        return {"content": f"error! `{guild}` not in database"}
    feeder_messages: List[str] = guild_data[0].get("feeder_messages")
    if not feeder_messages:
        use_msg: str = (
            f'use {use_prefix(message)}feeder-message add "<message>"!'
        )
        return {"content": f"no custom messages for `{guild}`! {use_msg}"}

    embeds: List[Embed] = []
    step = 5  # number of messages per embed
    for i in range(0, len(feeder_messages), step):
        embed = Embed(
            title="custom feeder messages",
            description="messsages randomly sent with the feeder alert",
        )
        value: str = ""
        for j in range(i, min(i + step, len(feeder_messages))):
            value += f"`{j+1}` {feeder_messages[j]} \n"
        embed.add_field(name="messages", value=value)
        embeds.append(embed)
    if len(feeder_messages) > step:
        return {"embed": embeds[0], "view": Menu(embeds)}
    return {"embed": embeds[0]}


async def feeder_message_delete(
    message: Union[ApplicationCommandInteraction, commands.Context],
) -> DiscordReturn:
    """delete custom message for feeder alert."""
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    guild_data: List = await db.get_guild_data(guild.id)
    if len(guild_data) == 0:
        return {"content": f"error! `{guild}` not in database"}
    feeder_messages: List[str] = guild_data[0].get("feeder_messages")
    if not feeder_messages:
        use_msg: str = (
            f'use {use_prefix(message)}feeder-message add "<message>"!'
        )
        return {"content": f"no custom messages for `{guild}`! {use_msg}"}
    return {
        "content": "choose messages to delete",
        "view": DeleterView(message, "feeder messages", feeder_messages),
    }


async def feeder_image_add(
    message: Union[
        ApplicationCommandInteraction, commands.Context, ModalInteraction
    ],
    new_image: str,
) -> DiscordReturn:
    """add custom image for feeder alert."""
    if len(new_image) > 100:
        return {"content": "url is too long! (max 100 characters)"}
    if not validate_url(new_image):
        return {"content": "invalid url!"}
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    guild_data: List = await db.get_guild_data(guild.id)
    if len(guild_data) == 0:
        return {"content": f"error! `{guild}` not in database"}
    feeder_images: Optional[List[str]] = guild_data[0].get("feeder_images")
    if feeder_images and len(feeder_images) >= 10:
        return {
            "content": "max number reached! delete before adding a new one!"
        }
    if feeder_images:
        feeder_images.append(new_image)
    else:
        feeder_images = [new_image]
    result: str = await db.update_guild_data(
        guild.id, feeder_images=feeder_images
    )
    if result.startswith("INSERT"):
        content: str = f"successfully added custom feeder image for `{guild}`"
    elif result.startswith("UPDATE"):
        content = f"successfully updated custom feeder image for `{guild}`"
    else:
        content = f"error updating custom feeder image for `{guild}`"
    return {"content": content}


async def feeder_image_show(
    message: Union[ApplicationCommandInteraction, commands.Context],
) -> DiscordReturn:
    """show custom images for feeder alert."""
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    guild_data: List = await db.get_guild_data(guild.id)
    if len(guild_data) == 0:
        return {"content": f"error! `{guild}` not in database"}
    feeder_images: Optional[List[str]] = guild_data[0].get("feeder_images")
    if not feeder_images:
        use_msg: str = f'use {use_prefix(message)}feeder-image add "<image>"!'
        return {"content": f"no custom image for `{guild}`! {use_msg}"}
    embeds: List[Embed] = []
    for image in feeder_images:
        embed = Embed(
            title="custom feeder images",
            description="images randomly sent with the feeder alert",
        )
        embed.set_image(url=image)
        embeds.append(embed)
    if len(feeder_images) > 1:
        return {"embed": embeds[0], "view": Menu(embeds)}
    return {"embed": embeds[0]}


async def feeder_image_delete(
    message: Union[ApplicationCommandInteraction, commands.Context],
) -> DiscordReturn:
    """delete custom image for feeder alert."""
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    guild_data: List = await db.get_guild_data(guild.id)
    if len(guild_data) == 0:
        return {"content": f"error! `{guild}` not in database"}
    feeder_images: Optional[List[str]] = guild_data[0].get("feeder_images")
    if not feeder_images:
        use_msg: str = f'use {use_prefix(message)}feeder-image add "<image>"!'
        return {"content": f"no custom image for `{guild}`! {use_msg}"}
    return {
        "content": "choose images to delete",
        "view": DeleterView(message, "feeder images", feeder_images),
    }


async def streaker_message_add(
    message: Union[
        ApplicationCommandInteraction, commands.Context, ModalInteraction
    ],
    new_message: str,
) -> DiscordReturn:
    """add custom message for streaker alert."""
    if len(new_message) > 100:
        return {"content": "message is too long! (max 100 characters)"}
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    guild_data: List = await db.get_guild_data(guild.id)
    if len(guild_data) == 0:
        return {"content": f"error! `{guild}` not in database"}
    streaker_messages: Optional[List] = guild_data[0].get("streaker_messages")
    if streaker_messages and len(streaker_messages) >= 25:
        return {
            "content": "max number reached! delete before adding a new one!"
        }
    if streaker_messages:
        streaker_messages.append(new_message)
    else:
        streaker_messages = [new_message]
    result: str = await db.update_guild_data(
        guild.id, streaker_messages=streaker_messages
    )
    if result.startswith("INSERT"):
        content: str = (
            f"successfully added custom streaker message for `{guild}`"
        )
    elif result.startswith("UPDATE"):
        content = f"successfully updated custom streaker message for `{guild}`"
    else:
        content = f"error updating custom streaker message for `{guild}`"
    return {"content": content}


async def streaker_message_show(
    message: Union[ApplicationCommandInteraction, commands.Context],
) -> DiscordReturn:
    """show custom messages for streaker alert."""
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    guild_data: List = await db.get_guild_data(guild.id)
    if len(guild_data) == 0:
        return {"content": f"error! `{guild}` not in database"}
    streaker_messages: Optional[List[str]] = guild_data[0].get(
        "streaker_messages"
    )
    if not streaker_messages:
        use_msg: str = (
            f'use {use_prefix(message)}streaker-message add "<message>"!'
        )
        return {"content": f"no custom messages for `{guild}`! {use_msg}"}
    embeds: List[Embed] = []
    step = 5  # number of messages per embed
    for i in range(0, len(streaker_messages), step):
        embed = Embed(
            title="custom streaker messages",
            description="messsages randomly sent with the streaker alert",
        )
        value: str = ""
        for j in range(i, min(i + step, len(streaker_messages))):
            value += f"`{j+1}` {streaker_messages[j]} \n"
        embed.add_field(name="messages", value=value)
        embeds.append(embed)
    if len(streaker_messages) > step:
        return {"embed": embeds[0], "view": Menu(embeds)}
    return {"embed": embeds[0]}


async def streaker_message_delete(
    message: Union[ApplicationCommandInteraction, commands.Context],
) -> DiscordReturn:
    """delete custom message for streaker alert."""
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    guild_data: List = await db.get_guild_data(guild.id)
    if len(guild_data) == 0:
        return {"content": f"error! `{guild}` not in database"}
    streaker_messages: Optional[List[str]] = guild_data[0].get(
        "streaker_messages"
    )
    if not streaker_messages:
        use_msg: str = (
            f'use {use_prefix(message)}streaker-message add "<message>"!'
        )
        return {"content": f"no custom messages for `{guild}`! {use_msg}"}
    return {
        "content": "choose messages to delete",
        "view": DeleterView(message, "streaker messages", streaker_messages),
    }
