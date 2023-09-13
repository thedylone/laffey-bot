"""main file initializing the bot and loading cogs"""
import argparse
import os
import sys
from os.path import dirname, join
from typing import List, Optional

from disnake import Game, Guild, Intents, channel
from disnake.ext import commands
from dotenv import load_dotenv

from cogs.custom_help import help as custom_help
from helpers.db import db

dotenv_path: str = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)
BOT_TOKEN: Optional[str] = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("BOT_TOKEN missing")
    sys.exit(1)

DATABASE_URL: Optional[str] = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL missing")
    sys.exit(1)


DEFAULT_PREFIX: str = os.environ.get("DEFAULT_PREFIX", "?")
SLASH_ENABLED: str = os.environ.get("SLASH_ENABLED", "1")
PREFIX_ENABLED: str = os.environ.get("PREFIX_ENABLED", "1")
DEBUG_MODE = False


async def get_prefix(_bot, message) -> List[str]:
    """returns prefix for the guild"""
    custom_prefix: str = DEFAULT_PREFIX
    if not isinstance(message.channel, channel.DMChannel):
        guild_id: int = message.guild.id
        guild_data: list = await db.get_guild_data(guild_id)
        if len(guild_data) == 0:
            await db.update_guild_data(guild_id, prefix=DEFAULT_PREFIX)
        else:
            custom_prefix = guild_data[0].get("prefix")
    return commands.when_mentioned_or(custom_prefix)(_bot, message)


intents: Intents = Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
    help_command=custom_help.Help(),
)


@bot.event
async def on_guild_join(guild: Guild) -> None:
    """adds guild to database when bot joins a server"""
    await db.update_guild_data(guild.id, prefix=DEFAULT_PREFIX)
    msg: str = f"joined server {guild.name}"
    print(msg)
    if bot.owner:
        await bot.owner.send(msg)


@bot.event
async def on_guild_remove(guild: Guild) -> None:
    """removes guild from database when bot leaves a server"""
    await db.delete_guild_data(guild.id)
    msg: str = f"left server {guild.name}"
    print(msg)
    if bot.owner:
        await bot.owner.send(msg)


@bot.event
async def on_ready() -> None:
    """runs when bot is ready"""
    print(f"logged in {bot.user.name}")
    # set activity of the bot
    await bot.change_presence(
        activity=Game(f"with lolis | {DEFAULT_PREFIX}help")
    )
    await db.load_db(DATABASE_URL)


def autoload(command_type: str) -> None:
    """loads all cogs in the given folder"""
    for file in os.listdir(f"./cogs/{command_type}"):
        if not file.endswith(".py"):
            continue
        extension: str = file[:-3]
        try:
            bot.load_extension(f"cogs.{command_type}.{extension}")
            print(f"loaded '{extension}'")
        except commands.ExtensionNotFound as err:
            print("could not find extension: ", err)
        except commands.ExtensionFailed as err:
            print("failed to load extension: ", err)
        except commands.ExtensionAlreadyLoaded as err:
            print("extension already loaded: ", err)
        except commands.NoEntryPointError as err:
            print("extension has no setup function: ", err)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="run discord bot")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="run in debug mode",
    )
    args: argparse.Namespace = parser.parse_args()
    DEBUG_MODE = args.debug
    if not DEBUG_MODE:
        autoload("error")  # loads error handler
    autoload("background")  # loads background tasks
    autoload("contextmenu")  # lodas context menu commands
    if int(SLASH_ENABLED):
        print("slash commands enabled")
        autoload("slash")
    if int(PREFIX_ENABLED):
        print("prefix commands enabled")
        autoload("prefix")

# Login to Discord with the bot's token.
bot.run(BOT_TOKEN)
