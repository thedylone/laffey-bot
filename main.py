import os
import sys
import argparse
import disnake
from disnake.ext import commands

from helpers import db_helper
from cogs.help import help

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    print("BOT_TOKEN missing")
    sys.exit(1)

DEFAULT_PREFIX = os.environ.get("DEFAULT_PREFIX", "?")
SLASH_ENABLED = os.environ.get("SLASH_ENABLED", 1)
PREFIX_ENABLED = os.environ.get("PREFIX_ENABLED", 1)
DEBUG_MODE = False


async def get_prefix(bot, message):
    custom_prefix = DEFAULT_PREFIX
    if not isinstance(message.channel, disnake.channel.DMChannel):
        guild_id = message.guild.id
        guild_data = await db_helper.get_guild_data(bot, guild_id)
        if len(guild_data) == 0:
            await db_helper.update_guild_data(
                bot, guild_id, prefix=DEFAULT_PREFIX
            )
        else:
            custom_prefix = guild_data[0].get("prefix")
    return commands.when_mentioned_or(custom_prefix)(bot, message)


intents = disnake.Intents.default()
intents.message_content = True

# creating a commands.Bot() instance, and assigning it to "bot"
bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
    help_command=help.Help(),
)


@bot.event
async def on_guild_join(guild: disnake.Guild):
    await db_helper.update_guild_data(bot, guild.id, prefix=DEFAULT_PREFIX)
    print(f"joined server {guild.name}")


@bot.event
async def on_guild_remove(guild: disnake.Guild):
    await db_helper.delete_guild_data(bot, guild.id)
    print(f"left server {guild.name}")


# When the bot is ready, run this code.
@bot.event
async def on_ready():
    print(f"logged in {bot.user.name}")
    # set activity of the bot
    await bot.change_presence(
        activity=disnake.Game(f"with lolis | {DEFAULT_PREFIX}help")
    )
    await db_helper.create_db_pool(bot)
    await db_helper.create_guilds_table(bot)
    await db_helper.create_players_table(bot)
    await db_helper.create_waitlist_table(bot)
    bot.valorant_watch_cycle.start()


# removes default help command
# bot.remove_command("help")


def autoload(command_type: str) -> None:
    for file in os.listdir(f"./cogs/{command_type}"):
        if file.endswith(".py"):
            extension = file[:-3]
            try:
                bot.load_extension(f"cogs.{command_type}.{extension}")
                print(f"loaded '{extension}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                print(f"failed to load {extension}\n{exception}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="run discord bot")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="run in debug mode",
    )
    args = parser.parse_args()
    DEBUG_MODE = args.debug
    if not DEBUG_MODE:
        autoload("error")  # loads error handler
    autoload("background")  # loads background tasks
    autoload("contextmenu")  # lodas context menu commands
    if int(SLASH_ENABLED):
        autoload("slash")
    if int(PREFIX_ENABLED):
        autoload("prefix")

# Login to Discord with the bot's token.
bot.run(BOT_TOKEN)
