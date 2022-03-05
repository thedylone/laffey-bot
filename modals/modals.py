import disnake

import aiohttp
import time

from helpers import json_helper


class ValorantWatchModal(disnake.ui.Modal):
    def __init__(self) -> None:
        components = [
            disnake.ui.TextInput(
                label="Username",
                placeholder="Your username in game",
                custom_id="name",
                style=disnake.TextInputStyle.short,
                max_length=50,
            ),
            disnake.ui.TextInput(
                label="Tag (without #)",
                placeholder="12345",
                custom_id="tag",
                style=disnake.TextInputStyle.short,
                max_length=5,
            ),
        ]
        super().__init__(
            title="valorant watch", custom_id="valorant_watch", components=components
        )

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        await inter.response.defer()
        """add user's valorant info to the database"""
        guild_data = json_helper.load("guildData.json")
        guild_id = inter.guild_id
        player_data = json_helper.load("playerData.json")
        user_id = str(inter.user.id)
        name = inter.text_values["name"]
        tag = inter.text_values["tag"]
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.henrikdev.xyz/valorant/v1/account/{name}/{tag}"
            ) as request:
                # using this until access for riot api granted async with session.get(f'https://{region}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}?api_key={RIOT_TOKEN}') as request:
                if request.status == 200:
                    data = await request.json()
                    player_data[user_id] = {
                        "name": name,
                        "tag": tag,
                        "region": data["data"]["region"],
                        "puuid": data["data"]["puuid"],
                        "lastTime": time.time(),
                        "streak": 0,
                        "guild": guild_id,
                    }
                    await inter.edit_original_message(
                        content=f"<@{user_id}> database updated, user added. remove using /valorant-unwatch"
                    )
                    json_helper.save(player_data, "playerData.json")
                else:
                    await inter.edit_original_message(
                        content=f"<@{user_id}> error connecting, database not updated. please try again"
                    )

    async def on_error(self, error: Exception, inter: disnake.ModalInteraction) -> None:
        await inter.response.send_message("Oops, something went wrong.", ephemeral=True)
