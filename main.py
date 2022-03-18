import os

BOT_TOKEN = os.environ["BOT_TOKEN"]

import disnake
from disnake.ext import commands

from helpers import db_helper
from cogs.help import help


async def get_prefix(bot, message):
    custom_prefix = os.environ["DEFAULT_PREFIX"]
    if not isinstance(message.channel, disnake.channel.DMChannel):
        guild_id = message.guild.id
        guild_data = await db_helper.get_guild_data(bot, guild_id)
        if len(guild_data) == 0:
            await db_helper.update_guild_data(
                bot, guild_id, prefix=os.environ["DEFAULT_PREFIX"]
            )
        else:
            custom_prefix = guild_data[0].get("prefix")
    return commands.when_mentioned_or(custom_prefix)(bot, message)


# creating a commands.Bot() instance, and assigning it to "bot"
bot = commands.Bot(
    command_prefix=get_prefix,
    intents=disnake.Intents.default(),
    help_command=help.Help()
)


@bot.event
async def on_guild_join(guild: disnake.Guild):
    await db_helper.update_guild_data(
        bot, guild.id, prefix=os.environ["DEFAULT_PREFIX"]
    )
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
        activity=disnake.Game(f"with lolis | {os.environ['DEFAULT_PREFIX']}help")
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
    autoload("error")  # loads error handler
    autoload("background")  # loads background tasks
    autoload("contextmenu")  # lodas context menu commands
    if int(os.environ["SLASH_ENABLED"]):
        autoload("slash")
    if int(os.environ["PREFIX_ENABLED"]):
        autoload("prefix")

# Login to Discord with the bot's token.
bot.run(BOT_TOKEN)
