import os
import sys
import json

BOT_TOKEN = os.environ["BOT_TOKEN"]

import disnake
from disnake.ext import commands

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found!")
else:
    with open("config.json", encoding='utf-8') as file:
        config = json.load(file)

# creating a commands.Bot() instance, and assigning it to "bot"
bot = commands.Bot(command_prefix=config['prefix'], intents=disnake.Intents.default())

# When the bot is ready, run this code.
@bot.event
async def on_ready():
    print(f"logged in {bot.user.name}")
    #set activity of the bot
    await bot.change_presence(activity=disnake.Game(f"with lolis | {config['prefix']}help"))

# removes default help command
# bot.remove_command("help")

def autoLoad(command_type: str) -> None:
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
    autoLoad("error") # loads error handler
    autoLoad("background") # loads background tasks
    if config['slash']: autoLoad("slash")
    if config['normal']: autoLoad("normal")

# Login to Discord with the bot's token.
bot.run(BOT_TOKEN)