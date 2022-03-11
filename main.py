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
    if (
        isinstance(message.channel, disnake.channel.DMChannel)
        or str(message.guild.id) not in bot.guild_data
    ):
        custom_prefix = os.environ["DEFAULT_PREFIX"]
    else:
        custom_prefix = bot.guild_data[str(message.guild.id)]["prefix"]
    return commands.when_mentioned_or(custom_prefix)(bot, message)


# creating a commands.Bot() instance, and assigning it to "bot"
bot = commands.Bot(
    command_prefix=get_prefix,
    intents=disnake.Intents.default(),
    test_guilds=config["guilds"],
)


@bot.event
async def on_guild_join(guild):
    bot.guild_data[str(guild.id)] = {"prefix": os.environ["DEFAULT_PREFIX"]}
    json_helper.save(bot.guild_data, "guildData.json")


@bot.event
async def on_guild_remove(guild):
    del bot.guild_data[str(guild.id)]
    json_helper.save(bot.guild_data, "guildData.json")


# When the bot is ready, run this code.
@bot.event
async def on_ready():
    print(f"logged in {bot.user.name}")
    # set activity of the bot
    await bot.change_presence(
        activity=disnake.Game(f"with lolis | {os.environ['DEFAULT_PREFIX']}help")
    )
    # cache data
    bot.guild_data = json_helper.load("guildData.json")
    bot.player_data = json_helper.load("playerData.json")


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
    if int(os.environ["SLASH_ENABLED"]):
        autoload("slash")
    if int(os.environ["PREFIX_ENABLED"]):
        autoload("prefix")

# Login to Discord with the bot's token.
bot.run(BOT_TOKEN)
