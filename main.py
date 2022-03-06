import os
import sys
import json

BOT_TOKEN = os.environ["BOT_TOKEN"]

import disnake
from disnake.ext import commands

from helpers import json_helper

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found!")
else:
    with open("config.json", encoding="utf-8") as file:
        config = json.load(file)


def get_prefix(bot, message):
    guild_data = json_helper.load("guildData.json")
    if str(message.guild.id) not in guild_data:
        return os.environ["DEFAULT_PREFIX"]
    else:
        return guild_data[str(message.guild.id)]["prefix"]


# creating a commands.Bot() instance, and assigning it to "bot"
bot = commands.Bot(
    command_prefix=get_prefix,
    intents=disnake.Intents.default(),
    test_guilds=config["guilds"],
)


@bot.event
async def on_guild_join(guild):
    guild_data = json_helper.load("guildData.json")
    guild_data[str(guild.id)] = {"prefix": os.environ["DEFAULT_PREFIX"]}
    json_helper.save(guild_data, "guildData.json")


@bot.event
async def on_guild_remove(guild):
    guild_data = json_helper.load("guildData.json")
    del guild_data[str(guild.id)]
    json_helper.save(guild_data, "guildData.json")


# When the bot is ready, run this code.
@bot.event
async def on_ready():
    print(f"logged in {bot.user.name}")
    # set activity of the bot
    await bot.change_presence(
        activity=disnake.Game(f"with lolis | {os.environ['DEFAULT_PREFIX']}help")
    )


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
    autoload("error")  # loads error handler
    autoload("background")  # loads background tasks
    autoload("contextmenu")  # lodas context menu commands
    if config["slash_enabled"]:
        autoload("slash")
    if config["prefix_enabled"]:
        autoload("prefix")

# Login to Discord with the bot's token.
bot.run(BOT_TOKEN)
