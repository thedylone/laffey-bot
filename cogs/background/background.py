"""background tasks"""
import asyncio
from typing import List, Optional, Union

import aiohttp
from disnake import Guild, TextChannel, Thread, User
from disnake.abc import GuildChannel, PrivateChannel
from disnake.ext import tasks
from disnake.ext.commands import Bot, Cog

from helpers.db import Database, db
from helpers.helpers import DiscordReturn
from helpers.valorant_classes import Match, Player

session = aiohttp.ClientSession()


async def check_user_exists(bot: Bot, discord_id: int) -> bool:
    """checks if user is accessible to the bot and
    if user has data in the database

    parameters
    ----------
    bot: disnake.ext.commands.Bot
        bot instance
    discord_id: int
        discord id of the user to check

    returns
    -------
    bool
        True if user is accessible and has data in the database
    """
    if await bot.getch_user(discord_id) is None:
        return False
    if len(await db.get_player_data(discord_id)) == 0:
        return False
    return True


async def check_guild_channel(
    bot: Bot, guild_id: int, discord_id: int
) -> Optional[TextChannel]:
    """checks if guild is accessible to the bot

    if guild is accessible, retrieve the saved channel and check if the channel
    is accessible to the bot and exists in the guild

    if saved channel is not accessible or does not exist, send a warning to the
    guild's first channel and update the database

    if guild is not accessible, update the database with guild_id=0

    parameters
    ----------
    bot: disnake.ext.commands.Bot
        bot instance
    guild_id: int
        discord id of the guild to check
    discord_id: int
        discord id of the user to check and update

    returns
    -------
    Optional[disnake.TextChannel]
        the saved channel if it exists and is accessible to the bot
    """
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


async def wait_until_db_ready(db: Database) -> None:
    """waits until the database is ready

    this is to avoid the bot starting the cycle tasks before the database
    is ready. the database is ready when the loaded attribute is True

    parameters
    ----------
    db: helpers.db.Database
        database instance
    """
    while not db.loaded:
        await asyncio.sleep(0.5)


class Background(Cog):
    """background tasks

    starts the cycle tasks once the database is ready

    attributes
    ----------
    bot: disnake.ext.commands.Bot
        bot instance
    valorant_watch_cycle: disnake.ext.tasks.Loop
        task to loop through all players and check for new matches
    """

    def __init__(self, bot: Bot) -> None:
        """initialises the Background cog with the bot instance and starts the
        cycle tasks

        parameters
        ----------
        bot: disnake.ext.commands.Bot
            bot instance
        """
        self.bot: Bot = bot
        """bot instance"""
        self.valorant_watch_cycle.start()

    @tasks.loop()
    async def valorant_watch_cycle(self) -> None:
        """loops through all players and checks for new matches

        if a new match is found, trigger and send the alert
        """
        await wait_until_db_ready(db)
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
    """adds the Background cog to the bot

    required for `bot.load_extension` to work

    parameters
    ----------
    bot: disnake.ext.commands.Bot
        bot instance
    """
    bot.add_cog(Background(bot))
