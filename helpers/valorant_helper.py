from turtle import update
import disnake
from disnake.ext import commands

import aiohttp
import time

from views.views import Menu, FeederMessagesView, FeederImagesView

from helpers import json_helper, db_helper


async def ping(bot: commands.Bot, message):
    """pings role and sends optional image"""
    """returns [content, file]"""
    guild_id = message.guild.id
    guild_data = await db_helper.get_guild_data(bot, guild_id)
    if len(guild_data) and guild_data[0].get("ping_role"):
        ping_role = guild_data[0].get("ping_role")
        return f"<@&{ping_role}>", disnake.File("jewelsignal.jpg")
    else:
        return (
            f"please set the role to ping first using {message.prefix if isinstance(message, commands.Context) else '/'}set-role!",
            None,
        )


async def info(bot: commands.Bot, message, user):
    """returns user's valorant info from the database"""
    """returns [content, embed]"""
    if user == None:
        user = message.author
    user_id = str(user.id)
    if user_id in bot.player_data:
        user_data = bot.player_data[user_id]
        embed = disnake.Embed(
            title="valorant info", description=f"<@{user_id}> saved info"
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(
            name="username",
            value=f"{user_data['name']}#{user_data['tag']}",
            inline=True,
        )
        embed.add_field(
            name="last updated", value=f"<t:{int(user_data['lastTime'])}>", inline=True
        )
        if len(user_data["headshots"]):
            embed.add_field(
                name="headshot %",
                value=f"{int(100 * sum(filter(None, user_data['headshots'])) / (sum(filter(None, user_data['headshots'])) + sum(filter(None, user_data['bodyshots'])) + sum(filter(None, user_data['legshots']))))}%",
                inline=False,
            )
            embed.add_field(
                name="ACS",
                value=f"{int(sum(user_data['acs']) / len(user_data['acs']))}",
                inline=True,
            )
            embed.set_footer(
                text=f"stats from last {len(user_data['headshots'])} recorded comp/unrated games"
            )
        return None, embed
    else:
        return (
            f"<@{user_id}> not in database! do {message.prefix if isinstance(message, commands.Context) else '/'}valorant-watch first",
            None,
        )


async def watch(bot: commands.Bot, message, name, tag):
    """add user's valorant info to the database"""
    """returns [content]"""
    if isinstance(message.channel, disnake.channel.DMChannel):
        guild_id = 0
    else:
        guild_id = message.guild.id
        guild_data = await db_helper.get_guild_data(bot, guild_id)
        if len(guild_data) == 0 or not guild_data[0].get("watch_channel"):
            return f"Please set the watch channel for the guild first using {message.prefix if isinstance(message, commands.Context) else '/'}set-channel! You can also DM me and I will DM you for each update instead!"

    user_id = str(message.author.id)
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.henrikdev.xyz/valorant/v1/account/{name}/{tag}"
        ) as account_request:
            # using this until access for riot api granted async with session.get(f'https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}?api_key={RIOT_TOKEN}') as request:
            if account_request.status != 200:
                return f"<@{user_id}> error connecting, database not updated. please try again (check if you have typed correctly)"
            account_data = await account_request.json()
            user_region = account_data["data"]["region"]
            user_puuid = account_data["data"]["puuid"]
        async with session.get(
            f"https://api.henrikdev.xyz/valorant/v3/by-puuid/matches/{user_region}/{user_puuid}"
        ) as match_request:
            if account_request.status != 200:
                return f"<@{user_id}> error connecting, database not updated. please try again (check if you have typed correctly)"
            match_data = await match_request.json()
            headshots, bodyshots, legshots, acs = [], [], [], []
            rounds_played = rounds_red = rounds_blue = streak = 0
            same_streak = True
            for latest_game in match_data["data"]:
                mode = latest_game["metadata"]["mode"]
                for round in latest_game["rounds"]:
                    rounds_played += round["end_type"] != "Surrendered"
                    rounds_red += round["winning_team"] == "Red"
                    rounds_blue += round["winning_team"] == "Blue"

                for player in latest_game["players"]["all_players"]:
                    if player["puuid"] == user_puuid:
                        player_stats = player["stats"]
                        player_team = player["team"]
                        break
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

                if mode != "Competitive" and mode != "Unrated":
                    continue
                acs.append(player_stats["score"] / rounds_played)
                headshots.append(player_stats["headshots"])
                bodyshots.append(player_stats["bodyshots"])
                legshots.append(player_stats["legshots"])

            bot.player_data[user_id] = {
                "guild": guild_id,
                "name": name,
                "tag": tag,
                "region": user_region,
                "puuid": user_puuid,
                "lastTime": time.time(),
                "streak": streak,
                "headshots": headshots,
                "bodyshots": bodyshots,
                "legshots": legshots,
                "acs": acs,
            }
            json_helper.save(bot.player_data, "playerData.json")
            return f"<@{user_id}> database updated, user added. remove using {message.prefix if isinstance(message, commands.Context) else '/'}valorant-unwatch"


async def unwatch(bot: commands.Bot, message):
    """removes user's valorant info from the database"""
    """returns [content]"""
    user_id = str(message.author.id)
    if user_id in bot.player_data:
        del bot.player_data[user_id]
        json_helper.save(bot.player_data, "playerData.json")
        content = f"<@{user_id}> database updated, user removed. add again using {message.prefix if isinstance(message, commands.Context) else '/'}valorant-watch"
    else:
        content = f"<@{user_id}> error updating, user not in database"
    return content


async def wait(bot: commands.Bot, message, *wait_users):
    """pings you when tagged user is done"""
    """returns [content]"""
    message_user_id = str(message.author.id)
    if len(wait_users) == 0:
        return f"<@{message_user_id}> use {message.prefix if isinstance(message, commands.Context) else '/'}valorant-wait <tag the user you are waiting for>"
    extra_message = ""
    success_waiting = []
    already_waiting = []
    not_in_database = []
    for wait_user in list(set(wait_users)):
        wait_user_id = str(wait_user.id)
        if wait_user_id == message_user_id:
            extra_message = "interesting but ok. "
        if wait_user_id in bot.player_data:
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


async def waitlist(bot: commands.Bot, message):
    """prints valorant waitlist"""
    """returns [embed]"""
    if isinstance(message.channel, disnake.channel.DMChannel):
        guild_id = 0
    else:
        guild_id = message.guild.id
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
            and bot.player_data[user_id]["guild"] == guild_id
        ):
            embed.add_field(name="user", value=f"<@{user_id}>", inline=False)
            embed.add_field(
                name="waiters",
                value=f"<@{'> <@'.join(bot.valorant_waitlist[user_id])}>",
            )
    return embed


async def set_channel(bot: commands.Bot, message, channel):
    """set the channel the bot will send updates to"""
    """returns [content]"""
    if channel == None:
        channel = message.channel
    guild = message.guild
    await db_helper.update_guild_data(bot, guild.id, "watch_channel", channel.id)
    return f"successfully set `#{channel}` as watch channel for `{guild}`"


async def set_role(bot: commands.Bot, message, role):
    if role == None:
        return f"use {message.prefix if isinstance(message, commands.Context) else '/'}set-role <tag the role>"
    guild = message.guild
    await db_helper.update_guild_data(bot, guild.id, "ping_role", role.id)
    return f"successfully set role `{role}` as watch channel for `{guild}`"


async def feeder_message_add(bot: commands.Bot, message, new_message: str):
    """add custom message for feeder alert"""
    """returns [content]"""
    if len(new_message) > 100:
        return "message is too long!"
    guild = message.guild
    guild_data = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data):
        feeder_messages = guild_data[0].get("feeder_messages")
        if feeder_messages and len(feeder_messages) >= 25:
            return "max number of messages reached! delete one before adding a new one!"
        else:
            if feeder_messages:
                feeder_messages.append(new_message)
            else:
                feeder_messages = [new_message]
            await db_helper.update_guild_data(
                bot, guild.id, "feeder_messages", feeder_messages
            )
        return f"successfully added custom feeder message for `{guild}`"
    return "error! `{guild}` not in database"


async def feeder_message_show(bot: commands.Bot, message):
    """show custom messages for feeder alert"""
    """returns [content, embed, view]"""
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
        return (
            f'no custom messages for `{guild}`! add using {message.prefix if isinstance(message, commands.Context) else "/"}feeder-message add "<custom message>"!',
            None,
            None,
        )


async def feeder_message_delete(bot: commands.Bot, message):
    """delete custom message for feeder alert"""
    """returns [content, view]"""
    guild = message.guild
    guild_data = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) and guild_data[0].get("feeder_messages"):
        view = FeederMessagesView(bot, message, guild_data[0].get("feeder_messages"))
        return "choose messages to delete", view
    else:
        return (
            f'no custom messages for `{guild}`! add using {message.prefix if isinstance(message, commands.Context) else "/"}feeder-message add "<custom message>"!',
            None,
        )


async def feeder_image_add(bot: commands.Bot, message, new_image: str):
    """add custom image for feeder alert"""
    if len(new_image) > 100:
        return "url is too long!"
    guild = message.guild
    guild_data = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data):
        feeder_images = guild_data[0].get("feeder_images")
        if feeder_images and len(feeder_images) >= 10:
            return "max number of images reached! delete one before adding a new one!"
        else:
            if feeder_images:
                feeder_images.append(new_image)
            else:
                feeder_images = [new_image]
            await db_helper.update_guild_data(
                bot, guild.id, "feeder_images", feeder_images
            )
        return f"successfully added custom feeder image for `{guild}`"
    return "error! `{guild}` not in database"


async def feeder_image_show(bot: commands.Bot, message):
    """show custom images for feeder alert"""
    """returns [content, embed, view]"""
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
        return (
            f'no custom images for `{guild}`! add using {message.prefix if isinstance(message, commands.Context) else "/"}feeder-image add "<custom image>"!',
            None,
            None,
        )


async def feeder_image_delete(bot: commands.Bot, message):
    """delete custom image for feeder alert"""
    """returns [content, view]"""
    guild = message.guild
    guild_data = await db_helper.get_guild_data(bot, guild.id)
    if len(guild_data) and guild_data[0].get("feeder_images"):
        view = FeederImagesView(bot, message, guild_data[0].get("feeder_images"))
        return "choose images to delete", view
    else:
        return (
            f'no custom images for `{guild}`! add using {message.prefix if isinstance(message, commands.Context) else "/"}feeder-image add "<custom image>"!',
            None,
        )
