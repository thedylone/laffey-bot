import disnake
from disnake.ext import commands

from views.views import Menu, FeederMessagesView, FeederImagesView

from helpers import json_helper


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
