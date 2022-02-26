import disnake
from disnake.ext import tasks, commands

import os
import json
import aiohttp
import asyncio
import time
import sys

from helpers import json_helper

# RIOT_TOKEN = os.environ["RIOT_TOKEN"] not used at the moment

if not os.path.isfile("config.json"):
    sys.exit("'config.json' not found!")
else:
    with open("config.json") as file:
        config = json.load(file)

class Game(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # self.valorantcycle.start()

    @commands.slash_command(name='jewels',
                            description='ping jewels role',
                            guild_ids=config['guilds'])
    async def jewelsPing(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        """pings @jewels role and sends image"""
        await inter.edit_original_message(content="<@&943511061447987281>", file=disnake.File('jewelsignal.jpg'))

    @commands.slash_command(name='valorant-info',
                            description='view valorant data in database',
                            guild_ids=config['guilds'])
    async def valorantinfo(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        """returns user's valorant info from the database"""
        playerData = json_helper.load()
        user_id = str(inter.user.id)
        if user_id in playerData:
            user_data = playerData[user_id]
            embed = disnake.Embed(
                title="valorant info",
                description=f"<@{user_id}> saved info"
            )
            embed.set_thumbnail(
                url=inter.user.display_avatar.url
            )
            embed.add_field(
                name="username",
                value=f"{user_data['name']}",
                inline= True
            )
            embed.add_field(
                name="tag",
                value=f"#{user_data['tag']}",
                inline= True
            )
            embed.add_field(
                name="last updated",
                value=f"<t:{int(user_data['lastTime'])}>"
            )
            await inter.edit_original_message(embed=embed)
        else:
            await inter.edit_original_message(content=f"<@{user_id}> not in database! do /valorant-watch first")

    @commands.slash_command(name='valorant-watch',
                            description='adds user into database',
                            guild_ids=config['guilds'])
    async def valorantwatch(self, inter: disnake.ApplicationCommandInteraction, name: str, tag: str):
        await inter.response.defer()
        """add user's valorant info to the database"""
        playerData = json_helper.load()
        user_id = str(inter.user.id)
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.henrikdev.xyz/valorant/v1/account/{name}/{tag}') as request:
            # using this until access for riot api granted async with session.get(f'https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}?api_key={RIOT_TOKEN}') as request:
                if request.status == 200:
                    data = await request.json()
                    playerData[user_id] = {
                        'name': name,
                        'tag': tag,
                        'region': data['data']['region'],
                        'puuid': data['data']['puuid'],
                        'lastTime': time.time()
                    }
                    await inter.edit_original_message(content=f"<@{user_id}> database updated, user added. remove using /valorant-unwatch")
                    json_helper.save(playerData)
                else:
                    await inter.edit_original_message(content=f"<@{user_id}> error connecting, database not updated. please try again")

    @commands.slash_command(name='valorant-unwatch',
                            description='removes user from database',
                            guild_ids=config['guilds'])
    async def valorantunwatch(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        """removes user's valorant info from the database"""
        playerData = json_helper.load()
        user_id = str(inter.user.id)
        if user_id in playerData:
            del playerData[user_id]
            json_helper.save(playerData)
            await inter.edit_original_message(content=f"<@{user_id}> database updated, user removed. add again using /valorant-watch")
        else:
            await inter.edit_original_message(content=f"<@{user_id}> error updating, user not in database")

                          

def setup(bot: commands.Bot):
    bot.add_cog(Game(bot))
