"""helper functions not for bot commands"""

import re
from typing import TypedDict
import disnake


def validate_url(url: str) -> bool:
    """validates url"""
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
    """discord return type"""

    content: str
    embed: disnake.Embed
    file: disnake.File
    view: disnake.ui.View
    allowed_mentions: disnake.AllowedMentions
