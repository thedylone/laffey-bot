"""helper functions for valorant cog"""

import time
import aiohttp
from disnake import (
    Embed,
    File,
    User,
    Member,
    Guild,
    channel,
    ApplicationCommandInteraction,
    ModalInteraction,
    TextChannel,
    VoiceChannel,
    Thread,
    Role,
)
from disnake.ext import commands

from views.views import Menu, DeleterView

from helpers import db_helper
from helpers.helpers import validate_url, DiscordReturn


class Player:
    """class for valorant player"""

    API = "https://api.henrikdev.xyz/valorant"
    player_id: int = 0
    guild_id: int = 0
    name: str = ""
    tag: str = ""
    region: str | None = ""
    puuid: str | None = ""
    lasttime: int = 0
    streak: int = 0
    headshots: list[int | None] = []
    bodyshots: list[int | None] = []
    legshots: list[int | None] = []
    acs: list[float | None] = []

    def __init__(self, *datas: dict, **kwargs: dict) -> None:
        for data in datas:
            for key, value in data.items():
                setattr(self, key, value)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self) -> str:
        return f"{self.name}#{self.tag}"

    def __repr__(self) -> str:
        return f"{self.name}#{self.tag}"

    @staticmethod
    def sum_remove_none(_list: list) -> int | float:
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

    async def update_account_info(self) -> None:
        """get account info from api. updates puuid and region"""
        async with aiohttp.ClientSession() as session:
            account_request: aiohttp.ClientResponse = await session.get(
                f"{self.API}/v1/account/{self.name}/{self.tag}"
            )
        if account_request.status != 200:
            raise ConnectionError("error retrieving account info!")
        account_json: dict[str, dict] = await account_request.json()
        account_data: dict | None = account_json.get("data")
        if account_data is None:
            raise ConnectionError("error retrieving account info!")
        self.puuid = account_data.get("puuid")
        self.region = account_data.get("region")

    async def get_match_history(self) -> list[dict]:
        """get match history from api. returns list of matches"""
        async with aiohttp.ClientSession() as session:
            match_request: aiohttp.ClientResponse = await session.get(
                f"{self.API}/v3/by-puuid/matches/{self.region}/{self.puuid}"
            )
        if match_request.status != 200:
            raise ConnectionError("error retrieving match history!")
        match_json: dict[str, list] = await match_request.json()
        match_data: list | None = match_json.get("data")
        if match_data is None:
            raise ConnectionError("error retrieving match history!")
        return match_data

    def update_stats(self, game: dict) -> None:
        """update stats from game"""
        metadata: dict | None = game.get("metadata")
        rounds: list[dict] | None = game.get("rounds")
        players: dict[str, dict] | None = game.get("players")
        if metadata is None or rounds is None or players is None:
            return
        mode: str = metadata.get("mode")
        if mode == "Deathmatch":
            return
        # loop through rounds
        rounds_played: int = 0
        rounds_red: int = 0
        rounds_blue: int = 0
        for _round in rounds:
            rounds_played += _round.get("end_type") != "Surrendered"
            rounds_red += _round.get("winning_team") == "Red"
            rounds_blue += _round.get("winning_team") == "Blue"
        # look for user in all players
        all_players: list[dict] | None = players.get("all_players")
        if all_players is None:
            return
        player_stats: dict | None = None
        player_team: str | None = None
        for player in all_players:
            if player.get("puuid") == self.puuid:
                player_stats = player.get("stats")
                player_team = player.get("team")
                break
        if player_stats is None or player_team is None:
            return
        # update streak
        if player_team == "Red" and (rounds_red > rounds_blue):
            self.streak = max(self.streak + 1, 1)
        elif player_team == "Blue" and (rounds_blue > rounds_red):
            self.streak = min(self.streak - 1, -1)
        # only add stats for competitive/unrated
        if mode not in ("Competitive", "Unrated"):
            return
        self.acs = self.acs[-4:] + [player_stats.get("score") / rounds_played]
        self.headshots = self.headshots[-4:] + [player_stats.get("headshots")]
        self.bodyshots = self.bodyshots[-4:] + [player_stats.get("bodyshots")]
        self.legshots = self.legshots[-4:] + [player_stats.get("legshots")]

    async def update_db(self, bot: commands.Bot) -> str:
        """updates player data in database"""
        return await db_helper.update_player_data(
            bot,
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


def use_prefix(
    message: ApplicationCommandInteraction
    | commands.Context
    | ModalInteraction,
) -> str | None:
    """returns the prefix to use depending on message"""
    if isinstance(message, commands.Context):
        return message.prefix
    return "/"


async def ping(
    bot: commands.Bot,
    message: ApplicationCommandInteraction | commands.Context,
) -> DiscordReturn:
    """
    pings role and sends optional image.
    returns content, embed, file
    """
    if message.guild is None:
        guild_id = 0
    else:
        guild_id: int = message.guild.id
    guild_data: list = await db_helper.get_guild_data(bot, guild_id)
    if len(guild_data) == 0 or not guild_data[0].get("ping_role"):
        prefix: str | None = use_prefix(message)
        return {
            "content": f"please set the role first using {prefix}set-role!",
        }
    ping_role: int = guild_data[0].get("ping_role")
    if guild_data[0].get("ping_image"):
        url: str = guild_data[0].get("ping_image")
        embed: Embed = Embed().set_image(url=url)
        return {
            "content": f"<@&{ping_role}>",
            "embed": embed,
        }
    return {
        "content": f"<@&{ping_role}>",
        "file": File("jewelsignal.jpg"),
    }


async def ping_image_add(
    bot: commands.Bot,
    message: ApplicationCommandInteraction
    | commands.Context
    | ModalInteraction,
    new_image: str,
) -> DiscordReturn:
    """
    add custom image for ping.
    returns content
    """
    if len(new_image) > 100:
        return {
            "content": "url is too long! (max 100 characters)",
        }
    if not validate_url(new_image):
        return {
            "content": "invalid url!",
        }
    guild: Guild | None = message.guild
    if guild is None:
        return {
            "content": "error! guild not found!",
        }
    result: str = await db_helper.update_guild_data(
        bot, guild.id, ping_image=new_image
    )
    if result.startswith("INSERT"):
        content: str = f"successfully added custom ping image for `{guild}`"
    elif result.startswith("UPDATE"):
        content = f"successfully updated custom ping image for `{guild}`"
    else:
        content = f"error updating custom ping image for `{guild}`"
    return {
        "content": content,
    }


async def ping_image_show(
    bot: commands.Bot,
    message: ApplicationCommandInteraction | commands.Context,
) -> DiscordReturn:
    """
    show custom image for ping.
    returns content, embed
    """
    guild: Guild | None = message.guild
    if guild is None:
        return {
            "content": "error! guild not found!",
        }
    guild_data: list = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) == 0 or not guild_data[0].get("ping_image"):
        use_msg: str = (
            f'use {use_prefix(message)}ping-image add "<custom image>"!'
        )
        return {
            "content": f"no custom image for `{guild}`! {use_msg}",
        }
    ping_image: str = guild_data[0].get("ping_image")
    embed = Embed(
        title="custom ping image",
        description="image sent with the ping",
    )
    embed.set_image(url=ping_image)
    return {
        "embed": embed,
    }


async def ping_image_delete(
    bot: commands.Bot,
    message: ApplicationCommandInteraction | commands.Context,
) -> DiscordReturn:
    """
    delete custom image for ping
    returns content
    """
    guild: Guild | None = message.guild
    if guild is None:
        return {
            "content": "error! guild not found!",
        }
    result: str = await db_helper.update_guild_data(
        bot, guild.id, ping_image=None
    )
    if result.startswith("INSERT"):
        content: str = f"successfully deleted custom ping image for `{guild}`"
    elif result.startswith("UPDATE"):
        content = f"successfully deleted custom ping image for `{guild}`"
    else:
        content = f"error deleting custom ping image for `{guild}`"
    return {
        "content": content,
    }


async def info(
    bot: commands.Bot,
    message: ApplicationCommandInteraction | commands.Context,
    user: User | Member | None = None,
) -> DiscordReturn:
    """
    returns user's valorant info from the database.
    returns content, embed
    """
    if user is None:
        # if no user specified, use author
        user = message.author
    player_data: list = await db_helper.get_player_data(bot, user.id)
    if len(player_data) == 0:
        use_msg: str = f"use {use_prefix(message)}valorant-watch first!"
        return {
            "content": f"<@{user.id}> user not in database. {use_msg}",
        }

    player: Player = Player(player_data[0])
    # create embed
    embed = Embed(
        title="valorant info", description=f"<@{user.id}> saved info"
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(
        name="username",
        value=str(player),
        inline=True,
    )
    embed.add_field(
        name="last updated",
        value=f"<t:{int(player.lasttime)}>",
        inline=True,
    )
    if player.num_games():
        embed.add_field(
            name="headshot %",
            value=f"{player.avg_headshots():.0%}",
            inline=False,
        )
        embed.add_field(
            name="ACS",
            value=int(player.avg_acs()),
            inline=True,
        )
        embed.set_footer(
            text=f"from last {player.num_games()} recorded comp/unrated games"
        )
    return {"embed": embed}


async def watch(
    bot: commands.Bot,
    message: ApplicationCommandInteraction
    | commands.Context
    | ModalInteraction,
    name: str,
    tag: str,
) -> DiscordReturn:
    """
    add user's valorant info to the database.
    returns content
    """
    guild_id: int = 0
    if not isinstance(message.channel, channel.DMChannel) and message.guild:
        guild_id = message.guild.id
        guild_data: list = await db_helper.get_guild_data(bot, guild_id)
        if len(guild_data) == 0 or not guild_data[0].get("watch_channel"):
            use_msg: str = f"use {use_prefix(message)}set-channel first!"
            return {
                "content": f"<@{message.author.id}> {use_msg}",
            }

    tag = tag.replace("#", "")
    user_id: int = message.author.id
    player: Player = Player(
        {"player_id": user_id, "guild_id": guild_id, "name": name, "tag": tag},
    )
    await player.update_account_info()
    match_data: list = await player.get_match_history()
    # loop through games from oldest to newest
    for game in match_data[::-1]:
        player.update_stats(game)
    player.lasttime = int(time.time())
    result: str = await player.update_db(bot)
    if result.startswith("INSERT"):
        content: str = f"<@{user_id}> user added to database."
    elif result.startswith("UPDATE"):
        content = f"<@{user_id}> user updated in database."
    else:
        content = f"<@{user_id}> error updating, user not in database"
    return {"content": content}


async def unwatch(
    bot: commands.Bot,
    message: ApplicationCommandInteraction | commands.Context,
) -> DiscordReturn:
    """
    removes user's valorant info from the database.
    returns content
    """
    user_id: int = message.author.id
    user_data: list = await db_helper.get_player_data(bot, user_id)
    if len(user_data):
        await db_helper.delete_player_data(bot, user_id)
        use_msg: str = f"add again using {use_prefix(message)}valorant-watch!"
        content: str = f"<@{user_id}> user removed from database. {use_msg}"
    else:
        content = f"<@{user_id}> error updating, user not in database"
    return {
        "content": content,
    }


async def wait(
    bot: commands.Bot,
    message: ApplicationCommandInteraction | commands.Context,
    *wait_users: User,
) -> DiscordReturn:
    """
    pings you when tagged user(s) is/are done.
    returns content
    """
    message_user_id: int = message.author.id
    if len(wait_users) == 0:
        use_msg: str = f"use {use_prefix(message)}valorant-wait <tag the user>"
        return {
            "content": f"<@{message_user_id}> {use_msg}",
        }
    extra_message: str = ""
    success_waiting: list[int] = []
    already_waited: list[int] = []
    non_db: list[int] = []
    for wait_user_id in map(lambda user: user.id, wait_users):
        if wait_user_id == message_user_id:
            # if wait for self
            extra_message = "interesting but ok."
        # retrieve waitlist and player info
        player_data: list = await db_helper.get_players_join_waitlist(
            bot, wait_user_id
        )
        if len(player_data):
            current_waiters: list = player_data[0].get("waiting_id")
            if current_waiters:
                if message_user_id in current_waiters:
                    already_waited.append(wait_user_id)
                    continue
            else:
                current_waiters = []
            await db_helper.update_waitlist_data(
                bot, wait_user_id, current_waiters + [message_user_id]
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
    bot: commands.Bot,
    message: ApplicationCommandInteraction | commands.Context,
) -> DiscordReturn:
    """
    prints valorant waitlist.
    returns embed
    """
    guild_id: int = 0
    if not isinstance(message.channel, channel.DMChannel) and message.guild:
        guild_id = message.guild.id
    # create embed
    embed = Embed(
        title="valorant waitlist", description="waitlist of watched users"
    )
    embed.set_thumbnail(url="https://i.redd.it/pxwk9pc6q9n91.jpg")
    waitlist_data: list = await db_helper.get_waitlist_join_players(bot)
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
    return {
        "embed": embed,
    }


async def set_channel(
    bot: commands.Bot,
    message: ApplicationCommandInteraction | commands.Context,
    _channel: TextChannel | VoiceChannel | Thread | None = None,
) -> DiscordReturn:
    """
    set the channel the bot will send updates to.
    returns content
    """
    if _channel is None:
        channel_id: int = message.channel.id
    else:
        channel_id = _channel.id
    guild: Guild | None = message.guild
    if guild is None:
        return {
            "content": "error! guild not found!",
        }
    result: str = await db_helper.update_guild_data(
        bot, guild.id, watch_channel=channel_id
    )
    if result.startswith("INSERT"):
        content: str = (
            f"successfully set channel <#{channel_id}> for `{guild}`"
        )
    elif result.startswith("UPDATE"):
        content = f"successfully updated channel <#{channel_id}> for `{guild}`"
    else:
        content = f"error updating channel for `{guild}`"
    return {
        "content": content,
    }


async def set_role(
    bot: commands.Bot,
    message: ApplicationCommandInteraction | commands.Context,
    role: Role | None = None,
) -> DiscordReturn:
    """
    set the role to ping.
    returns content
    """
    if role is None:
        return {
            "content": f"use {use_prefix(message)}set-role <role>!",
        }
    guild: Guild | None = message.guild
    if guild is None:
        return {
            "content": "error! guild not found!",
        }
    result: str = await db_helper.update_guild_data(
        bot, guild.id, ping_role=role.id
    )
    if result.startswith("INSERT"):
        content: str = f"successfully set role `{role}` for `{guild}`"
    elif result.startswith("UPDATE"):
        content = f"successfully updated role `{role}` for `{guild}`"
    else:
        content = f"error updating role for `{guild}`"
    return {
        "content": content,
    }


# FEEDER MESSAGE FUNCTIONS


async def feeder_message_add(
    bot: commands.Bot,
    message: ApplicationCommandInteraction
    | commands.Context
    | ModalInteraction,
    new_message: str,
) -> DiscordReturn:
    """
    add custom message for feeder alert.
    returns content
    """
    if len(new_message) > 100:
        return {
            "content": "message is too long! (max 100 characters)",
        }
    guild: Guild | None = message.guild
    if guild is None:
        return {
            "content": "error! guild not found!",
        }
    guild_data: list = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) == 0:
        return {
            "content": f"error! `{guild}` not in database",
        }
    feeder_messages: list | None = guild_data[0].get("feeder_messages")
    if feeder_messages and len(feeder_messages) >= 25:
        return {
            "content": "max number reached! delete before adding a new one!",
        }
    if feeder_messages:
        feeder_messages.append(new_message)
    else:
        feeder_messages = [new_message]
    result: str = await db_helper.update_guild_data(
        bot, guild.id, feeder_messages=feeder_messages
    )
    if result.startswith("INSERT"):
        content: str = (
            f"successfully added custom feeder message for `{guild}`"
        )
    elif result.startswith("UPDATE"):
        content = f"successfully updated custom feeder message for `{guild}`"
    else:
        content = f"error updating custom feeder message for `{guild}`"
    return {
        "content": content,
    }


async def feeder_message_show(
    bot: commands.Bot,
    message: ApplicationCommandInteraction | commands.Context,
) -> DiscordReturn:
    """
    show custom messages for feeder alert.
    returns content, embed, view
    """
    guild: Guild | None = message.guild
    if guild is None:
        return {
            "content": "error! guild not found!",
        }
    guild_data: list = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) == 0:
        return {
            "content": f"error! `{guild}` not in database",
        }
    feeder_messages: list[str] = guild_data[0].get("feeder_messages")
    if not feeder_messages:
        use_msg: str = (
            f'use {use_prefix(message)}feeder-message add "<message>"!'
        )
        return {
            "content": f"no custom messages for `{guild}`! {use_msg}",
        }

    embeds: list[Embed] = []
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
    bot: commands.Bot,
    message: ApplicationCommandInteraction | commands.Context,
) -> DiscordReturn:
    """
    delete custom message for feeder alert.
    returns content, view
    """
    guild: Guild | None = message.guild
    if guild is None:
        return {
            "content": "error! guild not found!",
        }
    guild_data: list = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) == 0:
        return {
            "content": f"error! `{guild}` not in database",
        }
    feeder_messages: list[str] = guild_data[0].get("feeder_messages")
    if not feeder_messages:
        use_msg: str = (
            f'use {use_prefix(message)}feeder-message add "<message>"!'
        )
        return {
            "content": f"no custom messages for `{guild}`! {use_msg}",
        }
    return {
        "content": "choose messages to delete",
        "view": DeleterView(bot, message, "feeder messages", feeder_messages),
    }


# FEEDER IMAGE FUNCTIONS


async def feeder_image_add(
    bot: commands.Bot,
    message: ApplicationCommandInteraction
    | commands.Context
    | ModalInteraction,
    new_image: str,
) -> DiscordReturn:
    """
    add custom image for feeder alert.
    returns content
    """
    if len(new_image) > 100:
        return {
            "content": "url is too long! (max 100 characters)",
        }
    if not validate_url(new_image):
        return {
            "content": "invalid url!",
        }
    guild: Guild | None = message.guild
    if guild is None:
        return {
            "content": "error! guild not found!",
        }
    guild_data: list = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) == 0:
        return {
            "content": f"error! `{guild}` not in database",
        }
    feeder_images: list[str] | None = guild_data[0].get("feeder_images")
    if feeder_images and len(feeder_images) >= 10:
        return {
            "content": "max number reached! delete before adding a new one!",
        }
    if feeder_images:
        feeder_images.append(new_image)
    else:
        feeder_images = [new_image]
    result: str = await db_helper.update_guild_data(
        bot, guild.id, feeder_images=feeder_images
    )
    if result.startswith("INSERT"):
        content: str = f"successfully added custom feeder image for `{guild}`"
    elif result.startswith("UPDATE"):
        content = f"successfully updated custom feeder image for `{guild}`"
    else:
        content = f"error updating custom feeder image for `{guild}`"
    return {
        "content": content,
    }


async def feeder_image_show(
    bot: commands.Bot,
    message: ApplicationCommandInteraction | commands.Context,
) -> DiscordReturn:
    """
    show custom images for feeder alert.
    returns content, embed, view
    """
    guild: Guild | None = message.guild
    if guild is None:
        return {
            "content": "error! guild not found!",
        }
    guild_data: list = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) == 0:
        return {
            "content": f"error! `{guild}` not in database",
        }
    feeder_images: list[str] | None = guild_data[0].get("feeder_images")
    if not feeder_images:
        use_msg: str = f'use {use_prefix(message)}feeder-image add "<image>"!'
        return {
            "content": f"no custom image for `{guild}`! {use_msg}",
        }
    embeds: list[Embed] = []
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
    bot: commands.Bot,
    message: ApplicationCommandInteraction | commands.Context,
) -> DiscordReturn:
    """
    delete custom image for feeder alert.
    returns content, view
    """
    guild: Guild | None = message.guild
    if guild is None:
        return {
            "content": "error! guild not found!",
        }
    guild_data: list = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) == 0:
        return {
            "content": f"error! `{guild}` not in database",
        }
    feeder_images: list[str] | None = guild_data[0].get("feeder_images")
    if not feeder_images:
        use_msg: str = f'use {use_prefix(message)}feeder-image add "<image>"!'
        return {
            "content": f"no custom image for `{guild}`! {use_msg}",
        }
    return {
        "content": "choose images to delete",
        "view": DeleterView(bot, message, "feeder images", feeder_images),
    }


# STREAKER MESSAGE FUNCTIONS


async def streaker_message_add(
    bot: commands.Bot,
    message: ApplicationCommandInteraction
    | commands.Context
    | ModalInteraction,
    new_message: str,
) -> DiscordReturn:
    """
    add custom message for streaker alert.
    returns content
    """
    if len(new_message) > 100:
        return {
            "content": "message is too long! (max 100 characters)",
        }
    guild: Guild | None = message.guild
    if guild is None:
        return {
            "content": "error! guild not found!",
        }
    guild_data: list = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) == 0:
        return {
            "content": f"error! `{guild}` not in database",
        }
    streaker_messages: list | None = guild_data[0].get("streaker_messages")
    if streaker_messages and len(streaker_messages) >= 25:
        return {
            "content": "max number reached! delete before adding a new one!",
        }
    if streaker_messages:
        streaker_messages.append(new_message)
    else:
        streaker_messages = [new_message]
    result: str = await db_helper.update_guild_data(
        bot, guild.id, streaker_messages=streaker_messages
    )
    if result.startswith("INSERT"):
        content: str = (
            f"successfully added custom streaker message for `{guild}`"
        )
    elif result.startswith("UPDATE"):
        content = f"successfully updated custom streaker message for `{guild}`"
    else:
        content = f"error updating custom streaker message for `{guild}`"
    return {
        "content": content,
    }


async def streaker_message_show(
    bot: commands.Bot,
    message: ApplicationCommandInteraction | commands.Context,
) -> DiscordReturn:
    """
    show custom messages for streaker alert.
    returns content, embed, view
    """
    guild: Guild | None = message.guild
    if guild is None:
        return {
            "content": "error! guild not found!",
        }
    guild_data: list = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) == 0:
        return {
            "content": f"error! `{guild}` not in database",
        }
    streaker_messages: list[str] | None = guild_data[0].get(
        "streaker_messages"
    )
    if not streaker_messages:
        use_msg: str = (
            f'use {use_prefix(message)}streaker-message add "<message>"!'
        )
        return {
            "content": f"no custom messages for `{guild}`! {use_msg}",
        }
    embeds: list[Embed] = []
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
    bot: commands.Bot,
    message: ApplicationCommandInteraction | commands.Context,
) -> DiscordReturn:
    """
    delete custom message for streaker alert.
    returns content, view
    """
    guild: Guild | None = message.guild
    if guild is None:
        return {
            "content": "error! guild not found!",
        }
    guild_data: list = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) == 0:
        return {
            "content": f"error! `{guild}` not in database",
        }
    streaker_messages: list[str] | None = guild_data[0].get(
        "streaker_messages"
    )
    if not streaker_messages:
        use_msg: str = (
            f'use {use_prefix(message)}streaker-message add "<message>"!'
        )
        return {
            "content": f"no custom messages for `{guild}`! {use_msg}",
        }
    return {
        "content": "choose messages to delete",
        "view": DeleterView(
            bot, message, "streaker messages", streaker_messages
        ),
    }
