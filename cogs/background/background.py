"""background tasks"""
import asyncio
import aiohttp

from typing import Optional, List, Union

from disnake import Guild, TextChannel, User, Thread
from disnake.abc import GuildChannel, PrivateChannel
from disnake.ext import tasks
from disnake.ext.commands import Bot, Cog

from helpers.db_helper import db
from helpers.helpers import DiscordReturn
from helpers.valorant_helper import Player, Match

session = aiohttp.ClientSession()


async def check_user_exists(bot: Bot, discord_id: int) -> bool:
    """returns True if user exists in database and as Discord user"""
    if await bot.getch_user(discord_id) is None:
        return False
    if len(await db.get_player_data(discord_id)) == 0:
        return False
    return True


async def check_guild_channel(
    bot: Bot, guild_id: int, discord_id: int
) -> Optional[TextChannel]:
    """checks if guild and channel are accessible and"""
    guild_exists: Optional[Guild] = bot.get_guild(guild_id)
    guild_data: List = await db.get_guild_data(guild_id)
    if guild_exists in bot.guilds and len(guild_data):
        # bot is still in the guild
        watch_channel_id = guild_data[0].get("watch_channel")
        channel_exists: Optional[
            Union[GuildChannel, Thread, PrivateChannel]
        ] = bot.get_channel(watch_channel_id)
        guild_exists_channels: List[TextChannel] = guild_exists.text_channels
        if channel_exists in guild_exists_channels:
            # check if channel is still in the guild
            return channel_exists

        # sends a warning that guild exists but channel is gone
        await db.update_guild_data(guild_id, watch_channel=0)
        if guild_exists_channels:
            await guild_exists_channels[0].send(
                "The channel I am set to doesn't exist! Please set again."
            )
            return
    elif guild_id:
        # no longer have permission to DM user, just update guild data
        await db.update_player_data(discord_id, guild_id=0)


class Background(Cog):
    """background tasks"""

    def __init__(self, bot: Bot) -> None:
        self.bot: Bot = bot
        self.valorant_watch_cycle.start()

    async def wait_until_db_ready(self) -> None:
        """waits until the database is ready"""
        while not db.loaded:
            await asyncio.sleep(0.5)

    @tasks.loop()
    async def valorant_watch_cycle(self) -> None:
        await self.wait_until_db_ready()
        init_list: List[dict] = await db.get_all_players()
        players: List[Player] = [Player(data) for data in init_list]
        for player in players:
            if not await check_user_exists(self.bot, player.player_id):
                # delete user?
                continue
            channel: Optional[
                Union[TextChannel, User]
            ] = await check_guild_channel(
                self.bot, player.guild_id, player.player_id
            ) or await self.bot.getch_user(
                player.player_id
            )
            if channel is None:
                continue
            matches: List[Match] = await player.get_match_history()
            for match in matches:
                if match.game_end <= player.lasttime:
                    continue
                alert: Optional[DiscordReturn] = await match.trigger_alert(
                    player, players
                )
                if alert is None:
                    continue
                await channel.send(**alert)
            # sleeps for number of seconds (avoid rate limit)
            await asyncio.sleep(0.5)


def setup(bot: Bot) -> None:
    bot.add_cog(Background(bot))
