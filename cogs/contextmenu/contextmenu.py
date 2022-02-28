import disnake
from disnake.ext import commands

import os
import json
import aiohttp
import time
import sys

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found!")
else:
    with open("config.json", encoding='utf-8') as file:
        config = json.load(file)

class ContextMenu(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    @commands.user_command(name="avatar")
    async def avatar(self, inter: disnake.ApplicationCommandInteraction, user: disnake.User):
        embed = disnake.Embed(title=f"{user}'s avatar")
        embed.set_image(url=user.display_avatar.url)
        await inter.response.send_message(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(ContextMenu(bot))