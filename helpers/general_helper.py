"""helper functions for general cog"""

import os
import re
import aiohttp
import dateutil.parser as dp
from disnake import Embed, ApplicationCommandInteraction
from disnake.ext import commands

from views.views import Menu, PageView, SelectEmbed

from helpers import db_helper
from helpers.helpers import DiscordReturn


HOLODEX_TOKEN: str | None = os.environ.get("HOLODEX_TOKEN")
HOLO_DESC = "[live and upcoming videos](https://holodex.net/)"
HOLO_IMG = "https://i.redd.it/lmrrc51ywma61.jpg"

NO_STREAM_EMBED: Embed = (
    Embed(
        title="hololive",
        description=HOLO_DESC,
    )
    .set_thumbnail(url=HOLO_IMG)
    .add_field(name="sadger badger", value="no strim rn", inline=False)
)


class Channel:
    """Channel class"""

    def __init__(self, name: str, emoji: str, color: int) -> None:
        self.name: str = name
        self.emoji: str = emoji
        self.color: int = color
        self.live_status = "isn't live :("
        self.embed = Embed(
            title=name,
            description=HOLO_DESC,
        )
        self.videos: list[dict] = []

    @staticmethod
    def convert_video(video: dict) -> dict[str, str | None]:
        """convert video from data"""
        channel: dict | None = video.get("channel")
        channel_id: str | None = None
        channel_name: str | None = None
        channel_photo: str | None = None
        if channel:
            channel_id = channel.get("id")
            channel_name = channel.get("name")
            channel_photo = channel.get("photo")
        status: str | None = video.get("status")
        time: str | None = video.get("start_scheduled")
        timestamp: str = str(dp.parse(time).timestamp()) if time else "0"
        title: str | None = video.get("title")
        if title:
            title = re.sub(r"\[|\]", "", title)
        video_id: str | None = video.get("id")
        link: str = f"https://www.youtube.com/watch?v={video_id}"
        string: str = (
            f"{status} <t:{int(float(timestamp))}:R>: [{title}]({link})"
        )
        return {
            "channel_id": channel_id,
            "channel_name": channel_name,
            "channel_photo": channel_photo,
            "status": status,
            "timestamp": timestamp,
            "title": title,
            "video_id": video_id,
            "link": link,
            "string": string,
        }

    def add_vid_to_embed(self, video: dict) -> None:
        """add video to embed"""
        data: dict[str, str | None] = self.convert_video(video)
        if data.get("status") == "live":
            self.live_status = "is live!"
        self.set_embed_thumbnail(data.get("channel_photo"))
        self.embed.add_field(
            name=data.get("status", ""),
            value=data.get("string"),
            inline=False,
        )

    def add_vids_to_embed(self, videos: list[dict]) -> None:
        """add videos to embed"""
        for vid in videos:
            self.add_vid_to_embed(vid)

    def set_embed_thumbnail(self, thumbnail: str | None) -> None:
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


async def holodex(data: dict) -> DiscordReturn:
    """
    get all live hololive videos.
    sends a request to the Holodex API.
    returns content, embed, view
    """
    if not data:
        # no videos available
        return {"embed": NO_STREAM_EMBED}
    embeds: list[Embed] = []
    step = 5  # number of vids per embed
    for i in range(0, len(data), step):
        embed: Embed = home_embed()
        for vid in data[i : i + step]:
            info: dict[str, str | None] = Channel.convert_video(vid)
            embed.add_field(
                name=info.get("channel_name", ""),
                value=info.get("string"),
                inline=False,
            )
        embeds.append(embed)
    if len(embeds) == 1:
        return {"embed": embeds[0]}
    return {
        "embed": embeds[0],
        "view": Menu(embeds),
    }


async def fubudex(data: dict) -> DiscordReturn:
    """
    get upcoming videos with a set dictionary of channels.
    sends a request to the Holodex API.
    returns content, embed, view
    """
    # store info for set channels
    focus_channels: dict[str, Channel] = {
        "UC1DCedRgGHBdm81E1llLhOQ": Channel("Pekora Ch. 兎田ぺこら", "👯", 0x64FFFF),
        "UCdn5BQ06XqgXoAxIhbqw5Rg": Channel("フブキCh。白上フブキ", "🌽", 0x64FFFF),
        "UC5CwaMl1eIgY8h02uZw7u8A": Channel("Suisei Channel", "☄️", 0x0064FF),
        "UChAnqc_AY5_I3Px5dig3X1Q": Channel("Korone Ch. 戌神ころね", "🥐", 0xFFFF00),
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
    embeds: list[SelectEmbed] = [
        SelectEmbed(
            name="home", description="main page", emoji="🏠", embed=_home_embed
        )
    ]
    for vid in data:
        info: dict[str, str | None] = Channel.convert_video(vid)
        channel_id: str | None = info.get("channel_id")
        if channel_id in focus_channels:
            focus_channels[channel_id].videos.append(vid)
        else:
            has_mention = True
            _mention_embed.add_field(
                name=info.get("channel_name", ""),
                value=info.get("string"),
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
    params: dict[str, str] = {
        "status": "live",
        "org": "Hololive",
        "limit": "50",
    }
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "X-APIKEY": HOLODEX_TOKEN,
    }
    async with aiohttp.ClientSession() as session:
        request: aiohttp.ClientResponse = await session.get(
            url, headers=headers, params=params
        )
    if request.status != 200:
        raise ConnectionError("error retrieving info! try again later")
    data: dict = await request.json()
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
    channel_list: list[str] = [
        "UC1DCedRgGHBdm81E1llLhOQ",
        "UCdn5BQ06XqgXoAxIhbqw5Rg",
        "UC5CwaMl1eIgY8h02uZw7u8A",
        "UChAnqc_AY5_I3Px5dig3X1Q",
    ]
    params: dict[str, str] = {"channels": ",".join(channel_list)}
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "X-APIKEY": HOLODEX_TOKEN,
    }
    async with aiohttp.ClientSession() as session:
        request: aiohttp.ClientResponse = await session.get(
            url, headers=headers, params=params
        )
    if request.status != 200:
        raise ConnectionError("error retrieving info! try again later")
    data: dict = await request.json()
    return await fubudex(data)


async def set_prefix(
    bot: commands.Bot,
    message: ApplicationCommandInteraction | commands.Context,
    prefix: str | None,
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
        result: str = await db_helper.update_guild_data(
            bot, guild_id, prefix=prefix
        )
        if result.startswith("INSERT"):
            content: str = f"prefix set to {prefix}"
        elif result.startswith("UPDATE"):
            content = f"prefix updated to {prefix}"
        else:
            content = "error updating prefix! try again later"
        return {"content": content}

    guild_data: list[dict] = await db_helper.get_guild_data(bot, guild_id)
    current_prefix: str | None = guild_data[0].get("prefix")
    use_prefix: str | None = (
        message.prefix if isinstance(message, commands.Context) else "/"
    )
    current_msg: str = f"current prefix: {current_prefix}"
    use_msg: str = f'use {use_prefix}prefix "<new prefix>"'
    info_msg = '(include "" for multiple worded prefix)'
    return {
        "content": f"{current_msg}\n{use_msg} {info_msg}",
    }
