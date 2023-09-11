"""helper functions for general cog"""

import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Union
import aiohttp
import dateutil.parser as dp
from disnake import Embed, ApplicationCommandInteraction
from disnake.ext import commands

from views.views import Menu, PageView, SelectEmbed

from helpers.db_helper import db
from helpers.helpers import DiscordReturn


HOLODEX_TOKEN: Optional[str] = os.environ.get("HOLODEX_TOKEN")
HOLO_DESC: str = "[live and upcoming videos](https://holodex.net/)"
HOLO_IMG: str = "https://i.redd.it/lmrrc51ywma61.jpg"

NO_STREAM_EMBED: Embed = (
    Embed(
        title="hololive",
        description=HOLO_DESC,
    )
    .set_thumbnail(url=HOLO_IMG)
    .add_field(name="sadger badger", value="no strim rn", inline=False)
)

# store info for set channels
CHANNELS: Dict[str, Dict] = {
    "UC1DCedRgGHBdm81E1llLhOQ": {
        "name": "Pekora Ch. 兎田ぺこら",
        "emoji": "👯",
        "color": 0x64FFFF,
    },
    "UCdn5BQ06XqgXoAxIhbqw5Rg": {
        "name": "フブキCh。白上フブキ",
        "emoji": "🌽",
        "color": 0x64FFFF,
    },
    "UC5CwaMl1eIgY8h02uZw7u8A": {
        "name": "Suisei Channel",
        "emoji": "☄️",
        "color": 0x0064FF,
    },
    "UChAnqc_AY5_I3Px5dig3X1Q": {
        "name": "Korone Ch. 戌神ころね",
        "emoji": "🥐",
        "color": 0xFFFF00,
    },
}


@dataclass
class YoutubeChannel:
    """class to store youtube channel data

    parameters
    ----------
    id: Optional[str]
        channel id
    name: Optional[str]
        channel name
    photo: Optional[str]
        channel photo url

    attributes
    ----------
    url: str
        channel url
    """

    id: str
    """channel id"""

    name: Optional[str]
    """channel name"""

    photo: Optional[str]
    """channel photo url"""

    @property
    def url(self) -> str:
        """returns channel url"""
        return f"https://www.youtube.com/channel/{self.id}"

    @staticmethod
    def from_dict(data: Dict) -> "YoutubeChannel":
        """convert to YoutubeChannel from data"""
        id: Optional[str] = data.get("id")
        if not id:
            raise ValueError("channel id not found!")
        return YoutubeChannel(
            id=id,
            name=data.get("name"),
            photo=data.get("photo"),
        )


@dataclass
class Video:
    """class to store video data"""

    id: str
    """video id"""

    channel: YoutubeChannel
    """video channel"""

    title: Optional[str]
    """video title"""

    status: Optional[str]
    """video status"""

    start_scheduled: Optional[str]
    """video scheduled start time"""

    @property
    def url(self) -> str:
        """returns video url"""
        return f"https://www.youtube.com/watch?v={self.id}"

    @property
    def timestamp(self) -> float:
        """returns video timestamp"""
        return (
            dp.parse(self.start_scheduled).timestamp()
            if self.start_scheduled
            else 0
        )

    def __str__(self) -> str:
        head: str = f"{self.status} <t:{int(self.timestamp)}:R>:"
        body: str = f"[{self.title}]({self.url})"
        return f"{head} {body}"

    @staticmethod
    def from_dict(data: Dict) -> "Video":
        """convert to Video from data"""
        id: Optional[str] = data.get("id")
        if not id:
            raise ValueError("video id not found!")
        channel_data: Optional[Dict] = data.get("channel")
        if not channel_data:
            raise ValueError("channel data not found!")
        return Video(
            id=id,
            channel=YoutubeChannel.from_dict(channel_data),
            title=data.get("title"),
            status=data.get("status"),
            start_scheduled=data.get("start_scheduled"),
        )


class Channel:
    """Holodex Channel class"""

    def __init__(self, name: str, emoji: str, color: int) -> None:
        self.name: str = name
        self.emoji: str = emoji
        self.color: int = color
        self.live_status = "isn't live :("
        self.embed = Embed(
            title=name,
            description=HOLO_DESC,
        )
        self.videos: List[Video] = []

    def add_vid_to_embed(self, video: Video) -> None:
        """add video to embed"""
        if video.status == "live":
            self.live_status = "is live!"
        self.set_embed_thumbnail(video.channel.photo)
        self.embed.add_field(
            name=video.status,
            value=str(video),
            inline=False,
        )

    def add_vids_to_embed(self, videos: List[Video]) -> None:
        """add videos to embed"""
        for vid in videos:
            self.add_vid_to_embed(vid)

    def set_embed_thumbnail(self, thumbnail: Optional[str]) -> None:
        """set embed thumbnail"""
        self.embed.set_thumbnail(url=thumbnail)


def home_embed() -> Embed:
    """returns home embed"""
    return Embed(
        title="hololive",
        description=HOLO_DESC,
        color=0x5EDEEB,
    ).set_thumbnail(url=HOLO_IMG)


def mention_embed() -> Embed:
    """returns mention embed"""
    return Embed(
        title="mentioned streams",
        description="not on their channels",
        color=0x5EDEEB,
    ).set_thumbnail(url=HOLO_IMG)


async def holodex(data: Dict) -> DiscordReturn:
    """
    get all live hololive videos.
    sends a request to the Holodex API.
    returns content, embed, view
    """
    if not data:
        # no videos available
        return {"embed": NO_STREAM_EMBED}
    embeds: List[Embed] = []
    step = 5  # number of vids per embed
    for i in range(0, len(data), step):
        embed: Embed = home_embed()
        for vid in data[i : i + step]:
            video: Video = Video.from_dict(vid)
            embed.add_field(
                name=video.channel.name,
                value=str(video),
                inline=False,
            )
        embeds.append(embed)
    if len(embeds) == 1:
        return {"embed": embeds[0]}
    return {
        "embed": embeds[0],
        "view": Menu(embeds),
    }


async def fubudex(data: Dict) -> DiscordReturn:
    """
    get upcoming videos with a set dictionary of channels.
    sends a request to the Holodex API.
    returns content, embed, view
    """
    # store info for set channels
    focus_channels: Dict[str, Channel] = {
        link: Channel(**info) for link, info in CHANNELS.items()
    }
    if not data:
        # no videos available
        return {"embed": NO_STREAM_EMBED}
    # create home embed
    _home_embed: Embed = home_embed()
    # create mention embed
    has_mention = False
    _mention_embed: Embed = mention_embed()
    # create list of SelectEmbeds
    embeds: List[SelectEmbed] = [
        SelectEmbed(
            name="home", description="main page", emoji="🏠", embed=_home_embed
        )
    ]
    for vid in data:
        video: Video = Video.from_dict(vid)
        channel_id: str = video.channel.id
        if channel_id in focus_channels:
            focus_channels[channel_id].videos.append(video)
        else:
            has_mention = True
            _mention_embed.add_field(
                name=video.channel.name,
                value=str(video),
                inline=False,
            )

    for link, channel in focus_channels.items():
        channel.add_vids_to_embed(channel.videos)
        if channel.videos:
            embeds.append(
                SelectEmbed(
                    name=channel.name,
                    description=channel.emoji,
                    emoji=channel.emoji,
                    color=channel.color,
                    embed=channel.embed,
                )
            )
        url: str = f"https://www.youtube.com/channel/{link}"
        _home_embed.add_field(
            name=channel.name,
            value=f"[{channel.name}]({url}) {channel.live_status}",
            inline=False,
        )

    if has_mention:
        embeds.append(
            SelectEmbed(
                name="mention",
                description="videos not on the channels but are mentioned",
                emoji="💬",
                embed=_mention_embed,
            )
        )
    return {"embed": _home_embed, "view": PageView(embeds)}


async def holo() -> DiscordReturn:
    """
    get all live hololive videos.
    calls the holodex() function.
    returns content, embed, view
    """
    if not HOLODEX_TOKEN:
        return {
            "content": "no Holodex Token! contact the person running the bot"
        }
    url = "https://holodex.net/api/v2/live"
    params: Dict[str, str] = {
        "status": "live",
        "org": "Hololive",
        "limit": "50",
    }
    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "X-APIKEY": HOLODEX_TOKEN,
    }
    async with aiohttp.ClientSession() as session:
        request: aiohttp.ClientResponse = await session.get(
            url, headers=headers, params=params
        )
    if request.status != 200:
        raise ConnectionError("error retrieving info! try again later")
    data: Dict = await request.json()
    return await holodex(data)


async def fubu() -> DiscordReturn:
    """
    get upcoming videos for a set list of channels.
    calls the fubudex() function.
    returns content, embed, view
    """
    if not HOLODEX_TOKEN:
        return {
            "content": "no Holodex Token! contact the person running the bot"
        }
    url = "https://holodex.net/api/v2/users/live"
    params: Dict[str, str] = {"channels": ",".join(CHANNELS.keys())}
    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "X-APIKEY": HOLODEX_TOKEN,
    }
    async with aiohttp.ClientSession() as session:
        request: aiohttp.ClientResponse = await session.get(
            url, headers=headers, params=params
        )
    if request.status != 200:
        raise ConnectionError("error retrieving info! try again later")
    data: Dict = await request.json()
    return await fubudex(data)


async def set_prefix(
    message: Union[ApplicationCommandInteraction, commands.Context],
    prefix: Optional[str],
) -> DiscordReturn:
    """
    set prefix for the server.
    if prefix is not provided, shows the current prefix.
    returns content
    """
    if prefix:
        prefix = re.sub("[^ !#-&(-~]", "", prefix)
    if message.guild is None:
        return {
            "content": "this command can only be used in a server",
        }
    guild_id: int = message.guild.id
    if prefix:
        result: str = await db.update_guild_data(guild_id, prefix=prefix)
        if result.startswith("INSERT"):
            content: str = f"prefix set to {prefix}"
        elif result.startswith("UPDATE"):
            content = f"prefix updated to {prefix}"
        else:
            content = "error updating prefix! try again later"
        return {"content": content}

    guild_data: List[Dict] = await db.get_guild_data(guild_id)
    current_prefix: Optional[str] = guild_data[0].get("prefix")
    use_prefix: Optional[str] = (
        message.prefix if isinstance(message, commands.Context) else "/"
    )
    current_msg: str = f"current prefix: {current_prefix}"
    use_msg: str = f'use {use_prefix}set-prefix "<new prefix>"'
    info_msg = '(include "" for multiple worded prefix)'
    return {
        "content": f"{current_msg}\n{use_msg} {info_msg}",
    }
