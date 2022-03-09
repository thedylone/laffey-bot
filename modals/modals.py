import disnake

import aiohttp
import time

from helpers import json_helper, valorant_helper


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
        content = await valorant_helper.watch(
            inter, inter.text_values["name"], inter.text_values["tag"]
        )
        await inter.edit_original_message(content=content)

    async def on_error(self, error: Exception, inter: disnake.ModalInteraction) -> None:
        await inter.edit_original_message(content="Oops, something went wrong.")


class ValorantFeederMessageModal(disnake.ui.Modal):
    def __init__(self) -> None:
        components = [
            disnake.ui.TextInput(
                label="Custom Message",
                placeholder="custom message for feeder alert",
                custom_id="message",
                style=disnake.TextInputStyle.short,
                max_length=100,
            ),
        ]
        super().__init__(
            title="valorant feeder message",
            custom_id="valorant_feeder_message",
            components=components,
        )

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        await inter.response.defer()
        content = await valorant_helper.feeder_message_add(
            inter, inter.text_values["message"]
        )
        await inter.edit_original_message(content=content)

    async def on_error(self, error: Exception, inter: disnake.ModalInteraction) -> None:
        await inter.edit_original_message(content="Oops, something went wrong.")


class ValorantFeederImageModal(disnake.ui.Modal):
    def __init__(self) -> None:
        components = [
            disnake.ui.TextInput(
                label="Custom Image URL",
                placeholder="url of custom image for feeder alert",
                custom_id="url",
                style=disnake.TextInputStyle.short,
                max_length=100,
            ),
        ]
        super().__init__(
            title="valorant feeder image",
            custom_id="valorant_feeder_image",
            components=components,
        )

    async def callback(self, inter: disnake.ModalInteraction) -> None:
        await inter.response.defer()
        content = await valorant_helper.feeder_image_add(
            inter, inter.text_values["url"]
        )
        await inter.edit_original_message(content=content)

    async def on_error(self, error: Exception, inter: disnake.ModalInteraction) -> None:
        await inter.edit_original_message(content="Oops, something went wrong.")
