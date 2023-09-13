"""helper functions for valorant cog"""
from typing import List, Optional, Union

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

from helpers.db import db
from helpers.helpers import DiscordReturn, use_prefix, validate_url
from helpers.valorant_classes import Player
from views.views import DeleterView, Menu


async def ping(
    message: Union[ApplicationCommandInteraction, commands.Context],
) -> DiscordReturn:
    """pings the role set for the guild

    if no role is set, return error message to set the role first
    if custom image is set, send the image with the ping
    if no custom image is set, send the default image with the ping

    parameters
    ----------
    message: Union[ApplicationCommandInteraction, commands.Context]
        interaction instance to respond to

    returns
    -------
    DiscordReturn
        content: str
            ping the role or error message
        embed: disnake.Embed
            custom image if set
        file: disnake.File
            default image if custom image is not set
    """
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
        ApplicationCommandInteraction,
        commands.Context,
        ModalInteraction,
    ],
    new_image: str,
) -> DiscordReturn:
    """adds a custom image for `ping` for the guild into the database

    url of custom image must be valid and no more than 100 characters

    parameters
    ----------
    message: Union[
        ApplicationCommandInteraction, commands.Context, ModalInteraction
    ]
        interaction instance to respond to
    new_image: str
        url of the image to add

    returns
    -------
    DiscordReturn
        content: str
            success or error message
    """
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
    """shows the custom image for `ping` for the guild if set

    if no custom image is set, return error message to set the image first

    parameters
    ----------
    message: Union[ApplicationCommandInteraction, commands.Context]
        interaction instance to respond to

    returns
    -------
    DiscordReturn
        content: str
            error message if no custom image is set
        embed: disnake.Embed
            custom image if set
    """
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
    """deletes the custom image for `ping` for the guild if set

    returns
    -------
    DiscordReturn
        content: str
            success or error message
    """
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
    """retrieves the user's valorant info from the database

    if no user is specified, the author of the message is used

    parameters
    ----------
    message: Union[ApplicationCommandInteraction, commands.Context]
        interaction instance to respond to
    user: Optional[Union[disnake.User, disnake.Member]]
        user to retrieve info of (default: author of the message)

    returns
    -------
    DiscordReturn
        content: str
            error message if user is not in the database
        embed: disnake.Embed
            embed containing the user's valorant info
    """
    if user is None:
        # if no user specified, use author
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
    """adds the user's valorant info to the database

    parameters
    ----------
    message: Union[
        ApplicationCommandInteraction, commands.Context, ModalInteraction
    ]
        interaction instance to respond to
    name: str
        valorant username of the user to add
    tag: str
        valorant tag of the user to add

    returns
    -------
    DiscordReturn
        content: str
            success or error message
    """
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
    """removes the user's valorant info from the database

    parameters
    ----------
    message: Union[ApplicationCommandInteraction, commands.Context]
        interaction instance to respond to

    returns
    -------
    DiscordReturn
        content: str
            success or error message
    """
    user_id: int = message.author.id
    user_data: List = await db.get_player_data(user_id)
    if len(user_data):
        await db.delete_player_data(user_id)
        content: str = (
            f"<@{user_id}> user removed from database."
            + f" add again using {use_prefix(message)}valorant-watch!"
        )
    else:
        content = f"<@{user_id}> error updating, user not in database"
    return {"content": content}


async def wait(
    message: Union[ApplicationCommandInteraction, commands.Context],
    *wait_users: User,
) -> DiscordReturn:
    """pings you when tagged user(s) is/are done.

    allows you to wait for multiple users at once.

    parameters
    ----------
    message: Union[ApplicationCommandInteraction, commands.Context]
        interaction instance to respond to
    wait_users: disnake.User
        user(s) to wait for

    returns
    -------
    DiscordReturn
        content: str
            success or error message
    """
    message_user_id: int = message.author.id
    if len(wait_users) == 0:
        use_msg: str = f"use {use_prefix(message)}valorant-wait <tag the user>"
        return {"content": f"<@{message_user_id}> {use_msg}"}
    extra_message: str = ""
    success_waiting: List[str] = []
    already_waited: List[str] = []
    non_db: List[str] = []
    for wait_user_id in map(lambda user: user.id, wait_users):
        if wait_user_id == message_user_id:
            # if wait for self
            extra_message = "interesting but ok. "
        # retrieve waitlist and player info
        player_data: List = await db.get_players_join_waitlist(wait_user_id)
        if len(player_data):
            current_waiters: List = player_data[0].get("waiting_id")
            if current_waiters:
                if message_user_id in current_waiters:
                    already_waited.append(str(wait_user_id))
                    continue
            else:
                current_waiters = []
            await db.update_waitlist_data(
                wait_user_id, current_waiters + [message_user_id]
            )
            success_waiting.append(str(wait_user_id))
        else:
            non_db.append(str(wait_user_id))
    success_message: str = (
        f"you're now waiting for <@{'> and <@'.join(success_waiting)}>. "
        if success_waiting
        else ""
    )
    already_message: str = (
        f"you're still waiting for <@{'> and <@'.join(already_waited)}>. "
        if already_waited
        else ""
    )
    non_db_message: str = (
        f"<@{'> and <@'.join(non_db)}> not in database, unable to wait."
        if non_db
        else ""
    )
    return {
        "content": extra_message
        + f"<@{message_user_id}> "
        + success_message
        + already_message
        + non_db_message
    }


async def waitlist(
    message: Union[ApplicationCommandInteraction, commands.Context],
) -> DiscordReturn:
    """shows the waitlist of users you are waiting for, and list of users
    waiting for you

    if sent in a guild, show the waitlist of users you are waiting for whose
    guild is the same as the current guild

    else if sent in a DM, show the waitlist of all users you are waiting for
    but the waiters for each user is hidden for privacy

    parameters
    ----------
    message: Union[ApplicationCommandInteraction, commands.Context]
        interaction instance to respond to

    returns
    -------
    DiscordReturn
        embed: disnake.Embed
            embed containing the waitlist of users you are waiting for
    """
    guild_id: int = 0
    if not isinstance(message.channel, channel.DMChannel) and message.guild:
        guild_id = message.guild.id
    embed: Embed = Embed(
        title="valorant waitlist", description="waitlist of watched users"
    ).set_thumbnail(url="https://i.redd.it/pxwk9pc6q9n91.jpg")
    waitlist_data: List = await db.get_waitlist_join_players()
    for player in waitlist_data:
        player_id: int = player.get("player_id")
        waiters: List = player.get("waiting_id")
        if player_id == message.author.id:
            embed.add_field(name="waiting for", value=f"<@{player_id}>")
            embed.add_field(
                name="waiters",
                value=f"<@{'> <@'.join(map(str, waiters))}>",
            )
            embed.add_field(name="", value="", inline=False)
        elif guild_id == 0 and message.author.id in waiters:
            # not sent to guild
            embed.add_field(name="waiting for", value=f"<@{player_id}>")
            embed.add_field(name="waiters", value=f"<@{message.author.id}>")
            embed.add_field(name="", value="", inline=False)
        elif guild_id and player.get("guild_id") == guild_id:
            # guild waitlist
            embed.add_field(name="waiting for", value=f"<@{player_id}>")
            embed.add_field(
                name="waiters",
                value=f"<@{'> <@'.join(map(str, waiters))}>",
            )
            embed.add_field(name="", value="", inline=False)
    return {"embed": embed}


async def set_channel(
    message: Union[ApplicationCommandInteraction, commands.Context],
    _channel: Optional[Union[TextChannel, VoiceChannel, Thread]] = None,
) -> DiscordReturn:
    """sets the channel for the guild to send alerts to

    if no channel is specified, the channel the message was sent in is used

    parameters
    ----------
    message: Union[ApplicationCommandInteraction, commands.Context]
        interaction instance to respond to
    _channel: Optional[Union[disnake.TextChannel, disnake.VoiceChannel,
    disnake.Thread]]
        channel to set (default: channel the message was sent in)

    returns
    -------
    DiscordReturn
        content: str
            success or error message
    """
    channel_id: int = message.channel.id
    if _channel:
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
    """sets the role for the guild for `ping`

    if role is None, return error message to specify the role

    parameters
    ----------
    message: Union[ApplicationCommandInteraction, commands.Context]
        interaction instance to respond to
    role: Optional[disnake.Role]
        role to set

    returns
    -------
    DiscordReturn
        content: str
            success or error message
    """
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
    """adds a custom feeder alert message for the guild into the database

    message must be no more than 100 characters and total number of messages
    must not exceed 25

    parameters
    ----------
    message: Union[
        ApplicationCommandInteraction, commands.Context, ModalInteraction
    ]
        interaction instance to respond to
    new_message: str
        message to add

    returns
    -------
    DiscordReturn
        content: str
            success or error message
    """
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
        return {"content": "too many! delete a message to add a new one!"}
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
    """shows the custom feeder alert messages for the guild if set

    if no custom messages are set, return error message to set the messages
    first

    parameters
    ----------
    message: Union[ApplicationCommandInteraction, commands.Context]
        interaction instance to respond to

    returns
    -------
    DiscordReturn
        content: str
            error message if no custom messages are set
        embed: disnake.Embed
            embed containing the custom messages
        view: views.Menu
            menu to scroll through the messages if there are more than 5
    """
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    guild_data: List = await db.get_guild_data(guild.id)
    if len(guild_data) == 0:
        return {"content": f"error! `{guild}` not in database"}
    feeder_messages: List[str] = guild_data[0].get("feeder_messages")
    if not feeder_messages:
        return {
            "content": f"no custom messages for `{guild}`!"
            + f' use {use_prefix(message)}feeder-message add "<message>"!'
        }
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
    """deletes custom feeder alert message(s) for the guild from the database

    if no custom messages are set, return error message to set the messages
    first

    parameters
    ----------
    message: Union[ApplicationCommandInteraction, commands.Context]
        interaction instance to respond to

    returns
    -------
    DiscordReturn
        content: str
            error message if no custom messages are set
        view: views.DeleterView
            view to delete the messages
    """
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    guild_data: List = await db.get_guild_data(guild.id)
    if len(guild_data) == 0:
        return {"content": f"error! `{guild}` not in database"}
    feeder_messages: List[str] = guild_data[0].get("feeder_messages")
    if not feeder_messages:
        return {
            "content": f"no custom messages for `{guild}`!"
            + f' use {use_prefix(message)}feeder-message add "<message>"!'
        }
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
    """adds a custom feeder alert image for the guild into the database

    url of custom image must be valid and no more than 100 characters and total
    number of images must not exceed 10

    parameters
    ----------
    message: Union[
        ApplicationCommandInteraction, commands.Context, ModalInteraction
    ]
        interaction instance to respond to
    new_image: str
        url of the image to add

    returns
    -------
    DiscordReturn
        content: str
            success or error message
    """
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
    feeder_images: List[str] = guild_data[0].get("feeder_images", [])
    if len(feeder_images) >= 10:
        return {"content": "too many! delete an image to add a new one!"}
    result: str = await db.update_guild_data(
        guild.id, feeder_images=feeder_images.append(new_image)
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
    """shows custom feeder alert images for the guild if set

    if no custom images are set, return error message to set the images first

    parameters
    ----------
    message: Union[ApplicationCommandInteraction, commands.Context]
        interaction instance to respond to

    returns
    -------
    DiscordReturn
        content: str
            error message if no custom images are set
        embed: disnake.Embed
            embed containing the custom images
        view: views.Menu
            menu to scroll through the images if there are more than 1
    """
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    guild_data: List = await db.get_guild_data(guild.id)
    if len(guild_data) == 0:
        return {"content": f"error! `{guild}` not in database"}
    feeder_images: Optional[List[str]] = guild_data[0].get("feeder_images")
    if not feeder_images:
        return {
            "content": f"no custom images for `{guild}`!"
            + f' use {use_prefix(message)}feeder-image add "<image>"!'
        }
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
    """deletes custom feeder alert image(s) for the guild from the database

    if no custom images are set, return error message to set the images first

    parameters
    ----------
    message: Union[ApplicationCommandInteraction, commands.Context]
        interaction instance to respond to

    returns
    -------
    DiscordReturn
        content: str
            error message if no custom images are set
        view: views.DeleterView
            view to delete the images
    """
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    guild_data: List = await db.get_guild_data(guild.id)
    if len(guild_data) == 0:
        return {"content": f"error! `{guild}` not in database"}
    feeder_images: Optional[List[str]] = guild_data[0].get("feeder_images")
    if not feeder_images:
        return {
            "content": f"no custom images for `{guild}`!"
            + f' use {use_prefix(message)}feeder-image add "<image>"!'
        }
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
    """adds a custom streaker alert message for the guild into the database

    message must be no more than 100 characters and total number of messages
    must not exceed 25

    parameters
    ----------
    message: Union[
        ApplicationCommandInteraction, commands.Context, ModalInteraction
    ]
        interaction instance to respond to
    new_message: str
        message to add

    returns
    -------
    DiscordReturn
        content: str
            success or error message
    """
    if len(new_message) > 100:
        return {"content": "message is too long! (max 100 characters)"}
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    guild_data: List = await db.get_guild_data(guild.id)
    if len(guild_data) == 0:
        return {"content": f"error! `{guild}` not in database"}
    streaker_messages: List[str] = guild_data[0].get("streaker_messages", [])
    if len(streaker_messages) >= 25:
        return {"content": "too many! delete a message to add a new one!"}
    result: str = await db.update_guild_data(
        guild.id, streaker_messages=streaker_messages.append(new_message)
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
    """shows custom streaker alert messages for the guild if set

    if no custom messages are set, return error message to set the messages
    first

    parameters
    ----------
    message: Union[ApplicationCommandInteraction, commands.Context]
        interaction instance to respond to

    returns
    -------
    DiscordReturn
        content: str
            error message if no custom messages are set
        embed: disnake.Embed
            embed containing the custom messages
        view: views.Menu
            menu to scroll through the messages if there are more than 5
    """
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    guild_data: List = await db.get_guild_data(guild.id)
    if len(guild_data) == 0:
        return {"content": f"error! `{guild}` not in database"}
    streaker_messages: List[str] = guild_data[0].get("streaker_messages")
    if not streaker_messages:
        return {
            "content": f"no custom messages for `{guild}`!"
            + f' use {use_prefix(message)}streaker-message add "<message>"!'
        }
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
    """deletes custom streaker alert message(s) for the guild from the database

    if no custom messages are set, return error message to set the messages

    parameters
    ----------
    message: Union[ApplicationCommandInteraction, commands.Context]
        interaction instance to respond to

    returns
    -------
    DiscordReturn
        content: str
            error message if no custom messages are set
        view: views.DeleterView
            view to delete the messages
    """
    guild: Optional[Guild] = message.guild
    if guild is None:
        return {"content": "error! guild not found!"}
    guild_data: List = await db.get_guild_data(guild.id)
    if len(guild_data) == 0:
        return {"content": f"error! `{guild}` not in database"}
    streaker_messages: List[str] = guild_data[0].get("streaker_messages")
    if not streaker_messages:
        return {
            "content": f"no custom messages for `{guild}`!"
            + f' use {use_prefix(message)}streaker-message add "<message>"!'
        }
    return {
        "content": "choose messages to delete",
        "view": DeleterView(message, "streaker messages", streaker_messages),
    }
