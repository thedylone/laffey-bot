import disnake
from disnake.ext import commands

import os
import aiohttp
import re
import dateutil.parser as dp

from views.views import Menu, PageView

from helpers import json_helper


HOLODEX_TOKEN = os.environ["HOLODEX_TOKEN"]


async def holodex(message, url, params, headers):
    """returns [content, embed, view]"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as request:
            if request.status == 200:
                data = await request.json()
                if data:
                    embeds = []
                    step = 5  # number of vids per embed
                    for i in range(0, len(data), step):
                        embed = disnake.Embed(
                            title="hololive",
                            description="[live and upcoming videos](https://holodex.net/)",
                        )
                        embed.set_thumbnail(
                            url="https://hololive.hololivepro.com/wp-content/themes/hololive/images/head_l.png"
                        )
                        for video in data[i : i + step]:
                            pattern = "\[|\]"
                            embed.add_field(
                                name=video["channel"]["name"],
                                value=f"{video['status']} <t:{int(dp.parse(video['start_scheduled']).timestamp())}:R>: [{re.sub(pattern,'',video['title'])}](https://www.youtube.com/watch?v={video['id']})",
                                inline=False,
                            )
                        embeds.append(embed)
                    view = Menu(embeds) if len(data) > step else None
                    return None, embeds[0], view
                else:
                    embed = disnake.Embed(
                        title="hololive",
                        description="[live and upcoming videos](https://holodex.net/)",
                    )
                    embed.set_thumbnail(
                        url="https://hololive.hololivepro.com/wp-content/themes/hololive/images/head_l.png"
                    )
                    embed.add_field(
                        name="sadger badger", value="no strim rn", inline=False
                    )
                    return None, embed, None
            else:
                return (
                    f"<@{message.author.id}> error retrieving info! try again later",
                    None,
                    None,
                )


async def fubudex(message, url, params, headers):
    """returns [content, embed, view]"""

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
        async with session.get(url, headers=headers, params=params) as request:
            if request.status == 200:
                data = await request.json()
                if data:
                    channel_data = {}
                    pattern = "\[|\]"
                    for channel in params["channels"].split(","):
                        channel_data[channel] = {
                            "name": "",
                            "live_status": False,
                            "embed": disnake.Embed(
                                description="[live and upcoming videos](https://holodex.net/)",
                            ),
                        }
                    home_embed = disnake.Embed(
                        title="hololive",
                        description="[live and upcoming videos](https://holodex.net/)",
                        color=0x5EDEEB,
                    ).set_thumbnail(
                        url="https://hololive.hololivepro.com/wp-content/themes/hololive/images/head_l.png"
                    )
                    has_mention = False
                    mention_embed = disnake.Embed(
                        title="mentioned streams",
                        description="not on their channels",
                        color=0x5EDEEB,
                    ).set_thumbnail(
                        url="https://hololive.hololivepro.com/wp-content/themes/hololive/images/head_l.png"
                    )
                    embeds_dict = {
                        "home": {
                            "description": "main page",
                            "emoji": "🏠",
                            "embed": home_embed,
                        }
                    }
                    for video in data:
                        video_channel = video["channel"]["id"]
                        if video_channel in channel_data:
                            if video["status"] == "live":
                                channel_data[video_channel]["live_status"] = True
                            name = video["channel"]["name"]
                            channel_data[video_channel]["name"] = name
                            channel_data[video_channel]["embed"].title = name
                            channel_data[video_channel]["embed"].set_thumbnail(
                                url=video["channel"]["photo"]
                            )
                            channel_data[video_channel]["embed"].add_field(
                                name=video["status"],
                                value=f"<t:{int(dp.parse(video['start_scheduled']).timestamp())}:R>: [{re.sub(pattern,'',video['title'])}](https://www.youtube.com/watch?v={video['id']})",
                                inline=False,
                            )
                        else:
                            has_mention = True
                            mention_embed.add_field(
                                name=video["channel"]["name"],
                                value=f"{video['status']} <t:{int(dp.parse(video['start_scheduled']).timestamp())}:R>: [{re.sub(pattern,'',video['title'])}](https://www.youtube.com/watch?v={video['id']})",
                                inline=True,
                            )

                    for channel in channel_data:
                        if channel_data[channel]["name"]:
                            channel_data[channel]["embed"].color = id_name_convert[
                                channel
                            ]["color"]
                            embeds_dict[channel_data[channel]["name"]] = {
                                "description": "hololive",
                                "emoji": id_name_convert[channel]["emoji"],
                                "embed": channel_data[channel]["embed"],
                            }
                        else:
                            channel_data[channel]["name"] = id_name_convert[channel][
                                "name"
                            ]
                        home_embed.add_field(
                            name=channel_data[channel]["name"],
                            value=f'[{channel_data[channel]["name"]}](https://www.youtube.com/channel/{channel}) {"is live!" if channel_data[channel]["live_status"] else "is not live :("}',
                            inline=False,
                        )

                    if has_mention:
                        embeds_dict["mention"] = {
                            "description": "videos not on the channels but they are mentioned",
                            "emoji": "💬",
                            "embed": mention_embed,
                        }
                    return None, home_embed, PageView(embeds_dict)
                else:
                    embed = disnake.Embed(
                        title="hololive",
                        description="[live and upcoming videos](https://holodex.net/)",
                    )
                    embed.set_thumbnail(
                        url="https://hololive.hololivepro.com/wp-content/themes/hololive/images/head_l.png"
                    )
                    embed.add_field(
                        name="sadger badger", value="no strim rn", inline=False
                    )
                    return None, embed, None
            else:
                return (
                    f"<@{message.author.id}> error retrieving info! try again later",
                    None,
                    None,
                )


async def peko(message):
    """peko"""
    """returns [content, embed, view]"""
    url = "https://holodex.net/api/v2/users/live"
    params = {
        "channels": "UC1DCedRgGHBdm81E1llLhOQ,UCdn5BQ06XqgXoAxIhbqw5Rg,UC5CwaMl1eIgY8h02uZw7u8A,UChAnqc_AY5_I3Px5dig3X1Q"
    }
    headers = {"Content-Type": "application/json", "X-APIKEY": HOLODEX_TOKEN}
    return await holodex(message, url, params, headers)


async def holo(message):
    """all live hololive streams"""
    """returns [content, embed, view]"""
    url = "https://holodex.net/api/v2/live"
    params = {"status": "live", "org": "Hololive", "limit": "50"}
    headers = {"Content-Type": "application/json", "X-APIKEY": HOLODEX_TOKEN}
    return await holodex(message, url, params, headers)


async def fubu(message):
    """fubu"""
    """returns [content, embed, view]"""
    url = "https://holodex.net/api/v2/users/live"
    params = {
        "channels": "UC1DCedRgGHBdm81E1llLhOQ,UCdn5BQ06XqgXoAxIhbqw5Rg,UC5CwaMl1eIgY8h02uZw7u8A,UChAnqc_AY5_I3Px5dig3X1Q"
    }
    headers = {"Content-Type": "application/json", "X-APIKEY": HOLODEX_TOKEN}
    return await fubudex(message, url, params, headers)


async def prefix(bot: commands.Bot, message, prefix):
    """set prefix for the server"""
    """returns [content]"""
    if prefix == None:
        current_prefix = bot.guild_data[str(message.guild.id)]["prefix"]
        return f'current prefix: {current_prefix}\nuse {message.prefix if isinstance(message, commands.Context) else "/"}prefix "<new prefix>" (include "" for multiple worded prefix)'
    bot.guild_data[str(message.guild.id)]["prefix"] = prefix
    json_helper.save(bot.guild_data, "guildData.json")
    return f"<@{message.author.id}> successfully saved {prefix} as new server prefix"
