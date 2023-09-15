"""helper functions not for bot commands"""

import re
from typing import Optional, TypedDict, Union

from disnake import (
    AllowedMentions,
    ApplicationCommandInteraction,
    Embed,
    File,
    ModalInteraction,
)
from disnake.ext import commands
from disnake.ui import View


def validate_url(url: str) -> bool:
    """checks if url is valid

    parameters
    ----------
    url: str
        url link to check

    returns
    -------
    bool
        True if url is valid
    """
    regex: re.Pattern[str] = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return re.match(regex, url) is not None


class DiscordReturn(TypedDict, total=False):
    """discord return type

    attributes
    ----------
    content: str
        content to send
    embed: disnake.Embed
        embed to send
    file: disnake.File
        file to send
    view: disnake.ui.View
        view to send
    allowed_mentions: disnake.AllowedMentions
        allowed mentions to send
    """

    content: str
    embed: Embed
    file: File
    view: View
    allowed_mentions: AllowedMentions


def use_prefix(
    message: Union[
        ApplicationCommandInteraction, commands.Context, ModalInteraction
    ],
) -> Optional[str]:
    """prefix to use depending on the type message

    parameters
    ----------
    message: Union[disnake.ApplicationCommandInteraction,
    disnake.ext.commands.Context, disnake.ui.ModalInteraction]
        message to check

    returns
    -------
    Optional[str]
        prefix to use
    """
    if isinstance(message, commands.Context):
        return message.prefix
    return "/"
