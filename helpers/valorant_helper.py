import disnake
from disnake.ext import commands

import aiohttp
import time

from views.views import Menu, FeederMessagesView, FeederImagesView

from helpers import json_helper


async def ping(message):
    """pings role and sends optional image"""
    """returns [content, file]"""
    guild_id = message.guild.id
    guild_data = json_helper.load("guildData.json")
    if "ping_role" not in guild_data[str(guild_id)]:
        return (
            f"please set the role to ping first using {message.prefix if isinstance(message, commands.Context) else '/'}set-role!",
            None,
        )
    else:
        ping_role = guild_data[str(guild_id)]["ping_role"]
        return f"<@&{ping_role}>", disnake.File("jewelsignal.jpg")


async def info(message, user):
    """returns user's valorant info from the database"""
    """returns [content, embed]"""
    player_data = json_helper.load("playerData.json")
    if user == None:
        user = message.author
    user_id = str(user.id)
    if user_id in player_data:
        user_data = player_data[user_id]
        embed = disnake.Embed(
            title="valorant info", description=f"<@{user_id}> saved info"
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="username", value=f"{user_data['name']}", inline=True)
        embed.add_field(name="tag", value=f"#{user_data['tag']}", inline=True)
        embed.add_field(name="last updated", value=f"<t:{int(user_data['lastTime'])}>")
        return None, embed
    else:
        return (
            f"<@{user_id}> not in database! do {message.prefix if isinstance(message, commands.Context) else '/'}valorant-watch first",
            None,
        )


async def watch(message, name, tag):
    """add user's valorant info to the database"""
    """returns [content]"""
    if isinstance(message.channel, disnake.channel.DMChannel):
        guild_id = 0
    else:
        guild_data = json_helper.load("guildData.json")
        guild_id = message.guild.id
        if (
            str(guild_id) not in guild_data
            or "watch_channel" not in guild_data[str(guild_id)]
            or guild_data[str(guild_id)]["watch_channel"] == 0
        ):
            return f"Please set the watch channel for the guild first using {message.prefix if isinstance(message, commands.Context) else '/'}set-channel! You can also DM me and I will DM you for each update instead!"

    player_data = json_helper.load("playerData.json")
    user_id = str(message.author.id)
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.henrikdev.xyz/valorant/v1/account/{name}/{tag}"
        ) as request:
            # using this until access for riot api granted async with session.get(f'https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}?api_key={RIOT_TOKEN}') as request:
            if request.status == 200:
                data = await request.json()
                player_data[user_id] = {
                    "name": name,
                    "tag": tag,
                    "region": data["data"]["region"],
                    "puuid": data["data"]["puuid"],
                    "lastTime": time.time(),
                    "streak": 0,
                    "guild": guild_id,
                }
                json_helper.save(player_data, "playerData.json")
                content = f"<@{user_id}> database updated, user added. remove using {message.prefix if isinstance(message, commands.Context) else '/'}valorant-unwatch"
            else:
                content = f"<@{user_id}> error connecting, database not updated. please try again"
            return content


async def unwatch(message):
    """removes user's valorant info from the database"""
    """returns [content]"""
    player_data = json_helper.load("playerData.json")
    user_id = str(message.author.id)
    if user_id in player_data:
        del player_data[user_id]
        json_helper.save(player_data, "playerData.json")
        content = f"<@{user_id}> database updated, user removed. add again using {message.prefix if isinstance(message, commands.Context) else '/'}valorant-watch"
    else:
        content = f"<@{user_id}> error updating, user not in database"
    return content


async def wait(bot, message, *wait_users):
    """pings you when tagged user is done"""
    """returns [content]"""
    message_user_id = str(message.author.id)
    if len(wait_users) == 0:
        return f"<@{message_user_id}> use {message.prefix if isinstance(message, commands.Context) else '/'}valorant-wait <tag the user you are waiting for>"
    player_data = json_helper.load("playerData.json")
    extra_message = ""
    success_waiting = []
    already_waiting = []
    not_in_database = []
    for wait_user in list(set(wait_users)):
        wait_user_id = str(wait_user.id)
        if wait_user_id == message_user_id:
            extra_message = "interesting but ok. "
        if wait_user_id in player_data:
            if wait_user_id in bot.valorant_waitlist:
                if message_user_id in bot.valorant_waitlist[wait_user_id]:
                    already_waiting.append(wait_user_id)
                else:
                    bot.valorant_waitlist[wait_user_id] += [message_user_id]
                    success_waiting.append(wait_user_id)
            else:
                bot.valorant_waitlist[wait_user_id] = [message_user_id]
                success_waiting.append(wait_user_id)
        else:
            not_in_database.append(wait_user_id)
    success_message = (
        f"success, will notify when <@{'> <@'.join(success_waiting)}> {'is' if len(success_waiting) == 1 else 'are'} done. "
        if success_waiting
        else ""
    )
    already_message = (
        f"you are already waiting for <@{'> <@'.join(already_waiting)}>. "
        if already_waiting
        else ""
    )
    not_in_database_message = (
        f"<@{'> <@'.join(not_in_database)}> not in database, unable to wait."
        if not_in_database
        else ""
    )
    return f"{extra_message}<@{message_user_id}> {success_message}{already_message}{not_in_database_message}"


async def waitlist(bot, message):
    """prints valorant waitlist"""
    """returns [embed]"""
    if isinstance(message.channel, disnake.channel.DMChannel):
        guild_id = 0
    else:
        guild_id = message.guild.id
    player_data = json_helper.load("playerData.json")
    embed = disnake.Embed(
        title="valorant waitlist", description="waitlist of watched users"
    )
    embed.set_thumbnail(
        url="https://cdn.vox-cdn.com/uploads/chorus_image/image/66615355/VALORANT_Jett_Red_crop.0.jpg"
    )
    for user_id in bot.valorant_waitlist:
        if guild_id == 0 and message.author.id in bot.valorant_waitlist[user_id]:
            embed.add_field(name="user", value=f"<@{user_id}>", inline=False)
            embed.add_field(
                name="waiters",
                value=f"<@{message.author.id}>",
            )
        elif (
            user_id == str(message.author.id)
            or guild_id
            and player_data[user_id]["guild"] == guild_id
        ):
            embed.add_field(name="user", value=f"<@{user_id}>", inline=False)
            embed.add_field(
                name="waiters",
                value=f"<@{'> <@'.join(bot.valorant_waitlist[user_id])}>",
            )
    return embed


async def set_channel(message, channel):
    """set the channel the bot will send updates to"""
    """returns [content]"""
    if channel == None:
        channel = message.channel
    guild = message.guild
    guild_data = json_helper.load("guildData.json")
    guild_data[str(guild.id)]["watch_channel"] = channel.id
    json_helper.save(guild_data, "guildData.json")
    return f"successfully set `#{channel}` as watch channel for `{guild}`"


async def set_role(message, role):
    if role == None:
        return f"use {message.prefix if isinstance(message, commands.Context) else '/'}set-role <tag the role>"
    guild = message.guild
    guild_data = json_helper.load("guildData.json")
    guild_data[str(guild.id)]["ping_role"] = role.id
    json_helper.save(guild_data, "guildData.json")
    return f"successfully set role `{role}` as watch channel for `{guild}`"


async def feeder_message_add(message, new_message: str):
    """add custom message for feeder alert"""
    """returns [content]"""
    if len(new_message) > 100:
        return "message is too long!"
    guild = message.guild
    guild_data = json_helper.load("guildData.json")
    if "feeder_messages" not in guild_data[str(guild.id)]:
        guild_data[str(guild.id)]["feeder_messages"] = [new_message]
    elif (
        len(guild_data[str(guild.id)]["feeder_messages"]) == 25
    ):  # max number of choices for select
        return "max number of messages reached! delete one before adding a new one!"
    else:
        guild_data[str(guild.id)]["feeder_messages"] += [new_message]
    json_helper.save(guild_data, "guildData.json")
    return f"successfully added custom feeder message for `{guild}`"


async def feeder_message_show(message):
    """show custom messages for feeder alert"""
    """returns [content, embed, view]"""
    guild = message.guild
    guild_data = json_helper.load("guildData.json")
    if (
        "feeder_messages" not in guild_data[str(guild.id)]
        or not guild_data[str(guild.id)]["feeder_messages"]
    ):
        return (
            f'no custom messages for `{guild}`! add using {message.prefix if isinstance(message, commands.Context) else "/"}feeder-message add "<custom message>"!',
            None,
            None,
        )
    feeder_messages = guild_data[str(guild.id)]["feeder_messages"]
    embeds = []
    step = 5  # number of messages per embed
    for i in range(0, len(feeder_messages), step):
        embed = disnake.Embed(
            title="custom feeder messages",
            description="messsages randomly sent with the feeder alert",
        )
        value = ""
        for j, message in enumerate(feeder_messages[i : i + step]):
            value += f"`{i+j+1}` {message} \n"
        embed.add_field(name="messages", value=value)
        embeds.append(embed)
    view = Menu(embeds) if len(feeder_messages) > step else None
    return None, embeds[0], view


async def feeder_message_delete(message):
    """delete custom message for feeder alert"""
    """returns [content, view]"""
    guild = message.guild
    guild_data = json_helper.load("guildData.json")
    if (
        "feeder_messages" not in guild_data[str(guild.id)]
        or not guild_data[str(guild.id)]["feeder_messages"]
    ):
        return (
            f'no custom messages for `{guild}`! add using {message.prefix if isinstance(message, commands.Context) else "/"}feeder-message add "<custom message>"!',
            None,
        )
    else:
        view = FeederMessagesView(message)
        return "choose messages to delete", view


async def feeder_image_add(message, new_image: str):
    """add custom image for feeder alert"""
    if len(new_image) > 100:
        return "url is too long!"
    guild = message.guild
    guild_data = json_helper.load("guildData.json")
    if "feeder_images" not in guild_data[str(guild.id)]:
        guild_data[str(guild.id)]["feeder_images"] = [new_image]
    elif (
        len(guild_data[str(guild.id)]["feeder_images"]) == 10
    ):  # max number of embeds in one message
        return "max number of images reached! delete one before adding a new one!"
    else:
        guild_data[str(guild.id)]["feeder_images"] += [new_image]
    json_helper.save(guild_data, "guildData.json")
    return f"successfully added custom feeder image for `{guild}`"


async def feeder_image_show(message):
    """show custom images for feeder alert"""
    """returns [content, embed, view]"""
    guild = message.guild
    guild_data = json_helper.load("guildData.json")
    if (
        "feeder_images" not in guild_data[str(guild.id)]
        or not guild_data[str(guild.id)]["feeder_images"]
    ):
        return (
            f'no custom images for `{guild}`! add using {message.prefix if isinstance(message, commands.Context) else "/"}feeder-image add "<custom image>"!',
            None,
            None,
        )
    feeder_images = guild_data[str(guild.id)]["feeder_images"]
    embeds = []
    for image in feeder_images:
        embed = disnake.Embed(
            title="custom feeder images",
            description="images randomly sent with the feeder alert",
        )
        embed.set_image(url=image)
        embeds.append(embed)
    view = Menu(embeds) if len(feeder_images) > 1 else None
    return None, embeds[0], view


async def feeder_image_delete(message):
    """delete custom image for feeder alert"""
    """returns [content, view]"""
    guild = message.guild
    guild_data = json_helper.load("guildData.json")
    if (
        "feeder_images" not in guild_data[str(guild.id)]
        or not guild_data[str(guild.id)]["feeder_images"]
    ):
        return (
            f'no custom images for `{guild}`! add using {message.prefix if isinstance(message, commands.Context) else "/"}feeder-image add "<custom image>"!',
            None,
        )
    else:
        view = FeederImagesView(message)
        return "choose images to delete", view
