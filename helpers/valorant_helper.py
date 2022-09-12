import disnake
from disnake.ext import commands

import aiohttp
import time

from views.views import (
    Menu,
    FeederMessagesView,
    FeederImagesView,
    StreakerMessagesView,
)

from helpers import db_helper


def use_prefix(message):
    if isinstance(message, commands.Context):
        return message.prefix
    else:
        return "/"


def sum_remove_none(list):
    return sum(filter(None, list))


async def ping(bot: commands.Bot, message):
    """
    pings role and sends optional image.
    returns content, embed, file
    """
    guild_id = message.guild.id
    guild_data = await db_helper.get_guild_data(bot, guild_id)
    if len(guild_data) and guild_data[0].get("ping_role"):
        ping_role = guild_data[0].get("ping_role")
        if guild_data[0].get("ping_image"):
            url = guild_data[0].get("ping_image")
            embed = disnake.Embed().set_image(url=url)
            return f"<@&{ping_role}>", embed, None
        return f"<@&{ping_role}>", None, disnake.File("jewelsignal.jpg")
    prefix = use_prefix(message)
    return (
        f"please set the role to ping first using {prefix}set-role!",
        None,
        None,
    )


async def ping_image_add(bot: commands.Bot, message, new_image: str):
    """
    add custom image for ping.
    returns content
    """
    if len(new_image) > 100:
        return "url is too long!"
    guild = message.guild
    await db_helper.update_guild_data(bot, guild.id, ping_image=new_image)
    return f"successfully added custom ping image for `{guild}`"


async def ping_image_show(bot: commands.Bot, message):
    """
    show custom image for ping.
    returns content, embed
    """
    guild = message.guild
    guild_data = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) and guild_data[0].get("ping_image"):
        ping_image = guild_data[0].get("ping_image")
        embed = disnake.Embed(
            title="custom ping image",
            description="image sent with the ping",
        )
        embed.set_image(url=ping_image)
        return None, embed
    use_msg = f'use {use_prefix(message)}ping-image add "<custom image>"!'
    return f"no custom image for `{guild}`! {use_msg}", None


async def ping_image_delete(bot: commands.Bot, message):
    """
    delete custom image for ping
    returns content
    """
    guild = message.guild
    await db_helper.update_guild_data(bot, guild.id, ping_image=None)
    return "ping image succesfully deleted"


async def info(bot: commands.Bot, message, user):
    """
    returns user's valorant info from the database.
    returns content, embed
    """
    if user is None:
        user = message.author
    player_data = await db_helper.get_player_data(bot, user.id)
    if len(player_data):
        user_data = player_data[0]
        name = user_data.get("name")
        tag = user_data.get("tag")
        lasttime = int(user_data.get("lasttime"))
        no_games = len(user_data.get("headshots"))
        # remove None from following stats and sum them
        headshots = sum_remove_none(user_data.get("headshots"))
        bodyshots = sum_remove_none(user_data.get("bodyshots"))
        legshots = sum_remove_none(user_data.get("legshots"))
        acs = sum_remove_none(user_data.get("acs"))
        # create embed
        embed = disnake.Embed(
            title="valorant info", description=f"<@{user.id}> saved info"
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(
            name="username",
            value=f"{name}#{tag}",
            inline=True,
        )
        embed.add_field(
            name="last updated",
            value=f"<t:{lasttime}>",
            inline=True,
        )
        if no_games:
            headshots
            embed.add_field(
                name="headshot %",
                value=f"{int(100*headshots/(headshots+bodyshots+legshots))}%",
                inline=False,
            )
            embed.add_field(
                name="ACS",
                value=f"{int(acs/no_games)}",
                inline=True,
            )
            embed.set_footer(
                text=f"stats from last {no_games} recorded comp/unrated games"
            )
        return None, embed

    use_msg = f"use {use_prefix(message)}valorant-watch first!"
    return (
        f"<@{user.id}> not in database! {use_msg}",
        None,
    )


async def watch(bot: commands.Bot, message, name, tag):
    """
    add user's valorant info to the database.
    returns content
    """
    if isinstance(message.channel, disnake.channel.DMChannel):
        guild_id = 0
    else:
        guild_id = message.guild.id
        guild_data = await db_helper.get_guild_data(bot, guild_id)
        if len(guild_data) == 0 or not guild_data[0].get("watch_channel"):
            use_msg = f"use {use_prefix(message)}set-channel first!"
            return f"set the guild's channel! {use_msg}"

    tag = tag.replace("#", "")
    user_id = message.author.id
    error = f"<@{user_id}> an error occured, please try again later"
    # retrieve account information
    session = aiohttp.ClientSession()
    api = "https://api.henrikdev.xyz/valorant"
    account_request = await session.get(f"{api}/v1/account/{name}/{tag}")
    if account_request.status != 200:
        return error
    account_data = await account_request.json()
    account_data = account_data.get("data")
    region = account_data.get("region")
    puuid = account_data.get("puuid")
    # retrieve recently played matches
    match_request = await session.get(
        f"{api}/v3/by-puuid/matches/{region}/{puuid}"
    )
    if match_request.status != 200:
        return error
    match_data = await match_request.json()
    match_data = match_data.get("data")
    await session.close()
    # initialise variables
    headshots, bodyshots, legshots, acs = [], [], [], []
    streak = 0
    same_streak = True
    # loop through games from newest to oldest
    for game in match_data:
        mode = game["metadata"]["mode"]
        if mode == "Deathmatch":
            continue
        rounds_played = rounds_red = rounds_blue = 0
        # loop through rounds
        for round in game["rounds"]:
            rounds_played += round["end_type"] != "Surrendered"
            rounds_red += round["winning_team"] == "Red"
            rounds_blue += round["winning_team"] == "Blue"
        # look for user in all players
        for player in game["players"]["all_players"]:
            if player["puuid"] == puuid:
                player_stats = player.get("stats")
                player_team = player.get("team")
                break
        # update streak, if not same_streak, skip
        if same_streak and player_team == "Red":
            if streak == 0 or not (streak > 0) ^ (rounds_red > rounds_blue):
                streak += 1 if rounds_red > rounds_blue else -1
            else:
                same_streak = False
        elif same_streak and player_team == "Blue":
            if streak == 0 or not (streak > 0) ^ (rounds_blue > rounds_red):
                streak += 1 if rounds_blue > rounds_red else -1
            else:
                same_streak = False
        # only add stats for competitive/unrated
        if mode != "Competitive" and mode != "Unrated":
            continue
        acs.append(player_stats.get("score") / rounds_played)
        headshots.append(player_stats.get("headshots"))
        bodyshots.append(player_stats.get("bodyshots"))
        legshots.append(player_stats.get("legshots"))

    await db_helper.update_player_data(
        bot,
        user_id,
        guild_id=guild_id,
        name=name,
        tag=tag,
        region=region,
        puuid=puuid,
        lasttime=time.time(),
        streak=streak,
        headshots=headshots,
        bodyshots=bodyshots,
        legshots=legshots,
        acs=acs,
    )
    return f"<@{user_id}> user added to database!"


async def unwatch(bot: commands.Bot, message):
    """
    removes user's valorant info from the database.
    returns content
    """
    user_id = message.author.id
    user_data = await db_helper.get_player_data(bot, user_id)
    if len(user_data):
        await db_helper.delete_player_data(bot, user_id)
        use_msg = f"add again using {use_prefix(message)}valorant-watch!"
        content = f"<@{user_id}> user removed from database. {use_msg}"
    else:
        content = f"<@{user_id}> error updating, user not in database"
    return content


async def wait(bot: commands.Bot, message, *wait_users):
    """
    pings you when tagged user is done.
    returns content
    """
    message_user_id = message.author.id
    if len(wait_users) == 0:
        use_msg = f"use {use_prefix(message)}valorant-wait <tag the user>"
        return f"<@{message_user_id}> incorrect usage. {use_msg}"
    extra_message = ""
    success_waiting = []
    already_waiting = []
    not_in_database = []
    for wait_user in list(set(wait_users)):
        wait_user_id = wait_user.id
        if wait_user_id == message_user_id:
            # if wait for self
            extra_message = "interesting but ok. "
        # retrieve waitlist and player info
        player_data = await db_helper.get_players_join_waitlist(
            bot, wait_user_id
        )
        if len(player_data):
            current_waiters = player_data[0].get("waiting_id")
            if current_waiters:
                if message_user_id in current_waiters:
                    already_waiting.append(wait_user_id)
                    continue
            else:
                current_waiters = []
            await db_helper.update_waitlist_data(
                bot, wait_user_id, current_waiters + [message_user_id]
            )
            success_waiting.append(wait_user_id)
        else:
            not_in_database.append(wait_user_id)
    success_users = "> <@".join(map(str, success_waiting))
    plural = "is" if len(success_waiting) == 1 else "are"
    success_message = (
        f"success, will notify when <@{success_users}> {plural} done. "
        if success_waiting
        else ""
    )
    already_users = "> <@".join(map(str, already_waiting))
    already_message = (
        f"you are already waiting for <@{already_users}>. "
        if already_waiting
        else ""
    )
    not_in_users = "> <@".join(map(str, not_in_database))
    not_in__message = (
        f"<@{not_in_users}> not in database, unable to wait."
        if not_in_database
        else ""
    )
    combined_message = f"{success_message}{already_message}{not_in__message}"
    return f"{extra_message}<@{message_user_id}> {combined_message}"


async def waitlist(bot: commands.Bot, message):
    """
    prints valorant waitlist.
    returns embed
    """
    if isinstance(message.channel, disnake.channel.DMChannel):
        guild_id = 0
    else:
        guild_id = message.guild.id
    # create embed
    embed = disnake.Embed(
        title="valorant waitlist", description="waitlist of watched users"
    )
    embed.set_thumbnail(url="https://i.redd.it/pxwk9pc6q9n91.jpg")
    waitlist_data = await db_helper.get_waitlist_join_players(bot)
    for waitlist_player in waitlist_data:
        player_id = waitlist_player.get("player_id")
        if guild_id == 0 and message.author.id in waitlist_player.get(
            "waiting_id"
        ):
            # not sent to guild, show all players the user is waiting for
            embed.add_field(name="user", value=f"<@{player_id}>", inline=False)
            embed.add_field(name="waiters", value=f"<@{message.author.id}>")
        elif (
            player_id == message.author.id
            or guild_id
            and waitlist_player.get("guild_id") == guild_id
        ):
            # sent to guild, show all waiters for user who set in current guild
            waiters = "> <@".join(map(str, waitlist_player.get("waiting_id")))
            embed.add_field(name="user", value=f"<@{player_id}>", inline=False)
            embed.add_field(name="waiters", value=f"<@{waiters}>")
    return embed


async def set_channel(bot: commands.Bot, message, channel):
    """
    set the channel the bot will send updates to.
    returns content
    """
    if channel is None:
        channel = message.channel
    guild = message.guild
    await db_helper.update_guild_data(bot, guild.id, watch_channel=channel.id)
    return f"successfully set `#{channel}` as watch channel for `{guild}`"


async def set_role(bot: commands.Bot, message, role):
    """
    set the role to ping.
    returns content
    """
    if role is None:
        return f"use {use_prefix(message)}set-role <tag the role>"
    guild = message.guild
    await db_helper.update_guild_data(bot, guild.id, ping_role=role.id)
    return f"successfully set role `{role}` as ping role for `{guild}`"


# FEEDER MESSAGE FUNCTIONS


async def feeder_message_add(bot: commands.Bot, message, new_message: str):
    """
    add custom message for feeder alert.
    returns content
    """
    if len(new_message) > 100:
        return "message is too long!"
    guild = message.guild
    guild_data = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data):
        feeder_messages = guild_data[0].get("feeder_messages")
        if feeder_messages and len(feeder_messages) >= 25:
            return "max number reached! delete before adding a new one!"
        else:
            if feeder_messages:
                feeder_messages.append(new_message)
            else:
                feeder_messages = [new_message]
            await db_helper.update_guild_data(
                bot, guild.id, feeder_messages=feeder_messages
            )
        return f"successfully added custom feeder message for `{guild}`"
    return "error! `{guild}` not in database"


async def feeder_message_show(bot: commands.Bot, message):
    """
    show custom messages for feeder alert.
    returns content, embed, view
    """
    guild = message.guild
    guild_data = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) and guild_data[0].get("feeder_messages"):
        feeder_messages = guild_data[0].get("feeder_messages")
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
    else:
        use_msg = f'use {use_prefix(message)}feeder-message add "<message>"!'
        return f"no custom messages for `{guild}`! {use_msg}", None, None


async def feeder_message_delete(bot: commands.Bot, message):
    """
    delete custom message for feeder alert.
    returns content, view
    """
    guild = message.guild
    guild_data = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) and guild_data[0].get("feeder_messages"):
        view = FeederMessagesView(
            bot, message, guild_data[0].get("feeder_messages")
        )
        return "choose messages to delete", view
    else:
        use_msg = f'use {use_prefix(message)}feeder-message add "<message>"!'
        return f"no custom messages for `{guild}`! {use_msg}", None


# FEEDER IMAGE FUNCTIONS


async def feeder_image_add(bot: commands.Bot, message, new_image: str):
    """
    add custom image for feeder alert.
    returns content
    """
    if len(new_image) > 100:
        return "url is too long!"
    guild = message.guild
    guild_data = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data):
        feeder_images = guild_data[0].get("feeder_images")
        if feeder_images and len(feeder_images) >= 10:
            return "max number reached! delete before adding a new one!"
        else:
            if feeder_images:
                feeder_images.append(new_image)
            else:
                feeder_images = [new_image]
            await db_helper.update_guild_data(
                bot, guild.id, feeder_images=feeder_images
            )
        return f"successfully added custom feeder image for `{guild}`"
    return "error! `{guild}` not in database"


async def feeder_image_show(bot: commands.Bot, message):
    """
    show custom images for feeder alert.
    returns content, embed, view
    """
    guild = message.guild
    guild_data = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) and guild_data[0].get("feeder_images"):
        feeder_images = guild_data[0].get("feeder_images")
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
    else:
        use_msg = f'use {use_prefix(message)}feeder-image add "<image>"!'
        return f"no custom image for `{guild}`! {use_msg}", None, None


async def feeder_image_delete(bot: commands.Bot, message):
    """
    delete custom image for feeder alert.
    returns content, view
    """
    guild = message.guild
    guild_data = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) and guild_data[0].get("feeder_images"):
        view = FeederImagesView(
            bot, message, guild_data[0].get("feeder_images")
        )
        return "choose images to delete", view
    else:
        use_msg = f'use {use_prefix(message)}feeder-image add "<image>"!'
        return f"no custom image for `{guild}`! {use_msg}", None


# STREAKER MESSAGE FUNCTIONS


async def streaker_message_add(bot: commands.Bot, message, new_message: str):
    """
    add custom message for streaker alert.
    returns content
    """
    if len(new_message) > 100:
        return "message is too long!"
    guild = message.guild
    guild_data = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data):
        streaker_messages = guild_data[0].get("streaker_messages")
        if streaker_messages and len(streaker_messages) >= 25:
            return "max number reached! delete before adding a new one!"
        else:
            if streaker_messages:
                streaker_messages.append(new_message)
            else:
                streaker_messages = [new_message]
            await db_helper.update_guild_data(
                bot, guild.id, streaker_messages=streaker_messages
            )
        return f"successfully added custom streaker message for `{guild}`"
    return "error! `{guild}` not in database"


async def streaker_message_show(bot: commands.Bot, message):
    """
    show custom messages for streaker alert.
    returns content, embed, view
    """
    guild = message.guild
    guild_data = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) and guild_data[0].get("streaker_messages"):
        streaker_messages = guild_data[0].get("streaker_messages")
        embeds = []
        step = 5  # number of messages per embed
        for i in range(0, len(streaker_messages), step):
            embed = disnake.Embed(
                title="custom streaker messages",
                description="messsages randomly sent with the streaker alert",
            )
            value = ""
            for j, message in enumerate(streaker_messages[i : i + step]):
                value += f"`{i+j+1}` {message} \n"
            embed.add_field(name="messages", value=value)
            embeds.append(embed)
        view = Menu(embeds) if len(streaker_messages) > step else None
        return None, embeds[0], view
    else:
        use_msg = f'use {use_prefix(message)}streaker-message add "<message>"!'
        return f"no custom messages for `{guild}`! {use_msg}", None, None


async def streaker_message_delete(bot: commands.Bot, message):
    """
    delete custom message for streaker alert.
    returns content, view
    """
    guild = message.guild
    guild_data = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) and guild_data[0].get("streaker_messages"):
        view = StreakerMessagesView(
            bot, message, guild_data[0].get("streaker_messages")
        )
        return "choose messages to delete", view
    else:
        use_msg = f'use {use_prefix(message)}streaker-message add "<message>"!'
        return f"no custom messages for `{guild}`! {use_msg}", None
