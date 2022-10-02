import disnake
from disnake.ext import commands

import os
import aiohttp
import re
import dateutil.parser as dp

from views.views import Menu, PageView, SelectEmbed

from helpers import db_helper


HOLODEX_TOKEN = os.environ.get("HOLODEX_TOKEN")
holo_desc = "[live and upcoming videos](https://holodex.net/)"
holo_url = "https://i.redd.it/lmrrc51ywma61.jpg"


async def holodex(message, url, params, headers):
    """
    get all live hololive videos.
    sends a request to the Holodex API.
    returns content, embed, view
    """
    async with aiohttp.ClientSession() as session:
        request = await session.get(url, headers=headers, params=params)
    if not request or request.status != 200:
        return (
            f"<@{message.author.id}> error retrieving info! try again later",
            None,
            None,
        )
    data = await request.json()
    if not data:
        # no videos available
        embed = disnake.Embed(
            title="hololive",
            description=holo_desc,
        )
        embed.set_thumbnail(url=holo_url)
        embed.add_field(
            name="sadger badger", value="no strim rn", inline=False
        )
        return None, embed, None

    embeds = []
    step = 5  # number of vids per embed
    for i in range(0, len(data), step):
        embed = disnake.Embed(
            title="hololive",
            description=holo_desc,
        )
        embed.set_thumbnail(url=holo_url)
        for video in data[i : i + step]:
            status = video.get("status")
            timestamp = int(dp.parse(video["start_scheduled"]).timestamp())
            title = re.sub(r"\[|\]", "", video.get("title"))
            link = f"https://www.youtube.com/watch?v={video.get('id')}"
            embed.add_field(
                name=video["channel"]["name"],
                value=f"{status} <t:{timestamp}:R>: [{title}]({link})",
                inline=False,
            )
        embeds.append(embed)
    view = Menu(embeds) if len(data) > step else None
    return None, embeds[0], view


async def fubudex(message, url, params, headers):
    """
    get upcoming videos with a set dictionary of channels.
    sends a request to the Holodex API.
    returns content, embed, view
    """
    # store info for set channels
    id_name_convert = {
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

    async with aiohttp.ClientSession() as session:
        request = await session.get(url, headers=headers, params=params)
    if not request or request.status != 200:
        return (
            f"<@{message.author.id}> error retrieving info! try again later",
            None,
            None,
        )
    data = await request.json()
    if not data:
        # no videos available
        embed = disnake.Embed(
            title="hololive",
            description=holo_desc,
        )
        embed.set_thumbnail(url=holo_url)
        embed.add_field(
            name="sadger badger", value="no strim rn", inline=False
        )
        return None, embed, None
    # create dictionary of channels requested
    channel_data = {}
    for channel in params["channels"].split(","):
        channel_data[channel] = {
            "name": "",
            "live_status": False,
            "embed": disnake.Embed(
                description=holo_desc,
            ),
        }
    # create home embed
    home_embed = disnake.Embed(
        title="hololive",
        description=holo_desc,
        color=0x5EDEEB,
    ).set_thumbnail(url=holo_url)
    # create mention embed
    has_mention = False
    mention_embed = disnake.Embed(
        title="mentioned streams",
        description="not on their channels",
        color=0x5EDEEB,
    ).set_thumbnail(url=holo_url)
    # create list of SelectEmbeds
    embeds = [
        SelectEmbed(
            name="home", description="main page", emoji="🏠", embed=home_embed
        )
    ]
    for video in data:
        id = video["channel"]["id"]
        name = video["channel"]["name"]
        status = video.get("status")
        timestamp = int(dp.parse(video["start_scheduled"]).timestamp())
        title = re.sub(r"\[|\]", "", video.get("title"))
        link = f"https://www.youtube.com/watch?v={video.get('id')}"
        if id in channel_data:
            # video channel is one of our requested channels
            if status == "live":
                channel_data[id]["live_status"] = True
            channel_data[id]["name"] = name
            # set information for channel's embed
            embed = channel_data[id]["embed"]
            embed.title = name
            embed.set_thumbnail(url=video["channel"]["photo"])
            embed.add_field(
                name=video["status"],
                value=f"<t:{timestamp}:R>: [{title}]({link})",
                inline=False,
            )
        else:
            # video channel is not our requested channel
            has_mention = True
            # add video to mention embed
            mention_embed.add_field(
                name=name,
                value=f"{status} <t:{timestamp}:R>: [{title}]({link})",
                inline=True,
            )

    for channel in channel_data:
        channel_name = channel_data[channel]["name"]
        if channel_name:
            # channel has video in data
            channel_data[channel]["embed"].color = id_name_convert[channel][
                "color"
            ]
            embeds.append(
                SelectEmbed(
                    name=channel_name,
                    description="hololive",
                    emoji=id_name_convert[channel]["emoji"],
                    embed=channel_data[channel]["embed"],
                )
            )
        else:
            # channel has no video in data
            channel_name = id_name_convert[channel]["name"]
        if channel_data[channel]["live_status"]:
            live_status = "is live!"
        else:
            live_status = "is not live :("
        channel_link = "https://www.youtube.com/channel/{channel}"
        # add info about channel to home embed
        home_embed.add_field(
            name=channel_name,
            value=f"[{channel_name}]({channel_link}) {live_status}",
            inline=False,
        )

    if has_mention:
        embeds.append(
            SelectEmbed(
                name="mention",
                description="videos not on the channels but are mentioned",
                emoji="💬",
                embed=mention_embed,
            )
        )
    return None, home_embed, PageView(embeds)


async def peko(message):
    """
    get upcoming videos for a set list of channels.
    calls the holodex() function.
    returns content, embed, view
    """
    if not HOLODEX_TOKEN:
        return (
            "no Holodex Token! contact the person running the bot",
            None,
            None,
        )
    url = "https://holodex.net/api/v2/users/live"
    channel_list = [
        "UC1DCedRgGHBdm81E1llLhOQ",
        "UCdn5BQ06XqgXoAxIhbqw5Rg",
        "UC5CwaMl1eIgY8h02uZw7u8A",
        "UChAnqc_AY5_I3Px5dig3X1Q",
    ]
    params = {"channels": ",".join(channel_list)}
    headers = {"Content-Type": "application/json", "X-APIKEY": HOLODEX_TOKEN}
    return await holodex(message, url, params, headers)


async def holo(message):
    """
    get all live hololive videos.
    calls the holodex() function.
    returns content, embed, view
    """
    if not HOLODEX_TOKEN:
        return (
            "no Holodex Token! contact the person running the bot",
            None,
            None,
        )
    url = "https://holodex.net/api/v2/live"
    params = {"status": "live", "org": "Hololive", "limit": "50"}
    headers = {"Content-Type": "application/json", "X-APIKEY": HOLODEX_TOKEN}
    return await holodex(message, url, params, headers)


async def fubu(message):
    """
    get upcoming videos for a set list of channels.
    calls the fubudex() function.
    returns content, embed, view
    """
    if not HOLODEX_TOKEN:
        return (
            "no Holodex Token! contact the person running the bot",
            None,
            None,
        )
    url = "https://holodex.net/api/v2/users/live"
    channel_list = [
        "UC1DCedRgGHBdm81E1llLhOQ",
        "UCdn5BQ06XqgXoAxIhbqw5Rg",
        "UC5CwaMl1eIgY8h02uZw7u8A",
        "UChAnqc_AY5_I3Px5dig3X1Q",
    ]
    params = {"channels": ",".join(channel_list)}
    headers = {"Content-Type": "application/json", "X-APIKEY": HOLODEX_TOKEN}
    return await fubudex(message, url, params, headers)


async def prefix(bot: commands.Bot, message, prefix):
    """
    set prefix for the server.
    if prefix is not provided, shows the current prefix.
    returns content
    """
    if prefix:
        prefix = re.sub("[^ !#-&(-~]", "", prefix)
    guild_id = message.guild.id
    if prefix:
        await db_helper.update_guild_data(bot, guild_id, prefix=prefix)
        author = message.author.id
        return f"<@{author}> successfully saved {prefix} as new server prefix"
    else:
        guild_data = await db_helper.get_guild_data(bot, guild_id)
        current_prefix = guild_data[0].get("prefix")
        if isinstance(message, commands.Context):
            use_prefix = message.prefix
        else:
            use_prefix = "/"
        current_msg = f"current prefix: {current_prefix}"
        use_msg = f'use {use_prefix}prefix "<new prefix>"'
        info_msg = '(include "" for multiple worded prefix)'
        return f"{current_msg}\n{use_msg} {info_msg}"
