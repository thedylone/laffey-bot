import disnake
from disnake.ext import commands

import os
import aiohttp
import re

from views.views import Menu

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
                                value=f"{video['status']}: [{re.sub(pattern,'',video['title'])}](https://www.youtube.com/watch?v={video['id']})",
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


async def prefix(bot: commands.Bot, message, prefix):
    """set prefix for the server"""
    """returns [content]"""
    if prefix == None:
        current_prefix = bot.guild_data[str(message.guild.id)]["prefix"]
        return f'current prefix: {current_prefix}\nuse {message.prefix if isinstance(message, commands.Context) else "/"}prefix "<new prefix>" (include "" for multiple worded prefix)'
    bot.guild_data[str(message.guild.id)]["prefix"] = prefix
    json_helper.save(bot.guild_data, "guildData.json")
    return f"<@{message.author.id}> successfully saved {prefix} as new server prefix"
