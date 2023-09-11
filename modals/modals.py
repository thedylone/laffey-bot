"""disnake modals"""

from disnake import ModalInteraction, TextInputStyle
from disnake.ui import TextInput, Modal

from helpers import valorant_helper


class ValorantWatchModal(Modal):
    """modal for adding a player to watch"""

    def __init__(self) -> None:
        components: list[TextInput] = [
            TextInput(
                label="Username",
                placeholder="Your username in game",
                custom_id="name",
                style=TextInputStyle.short,
                max_length=50,
            ),
            TextInput(
                label="Tag",
                placeholder="12345",
                custom_id="tag",
                style=TextInputStyle.short,
                max_length=5,
            ),
        ]
        super().__init__(
            title="valorant watch",
            custom_id="valorant_watch",
            components=components,
        )

    async def callback(self, interaction: ModalInteraction, /) -> None:
        await interaction.response.defer()
        await interaction.edit_original_message(
            **await valorant_helper.watch(
                interaction,
                interaction.text_values["name"],
                interaction.text_values["tag"],
            )
        )

    async def on_error(
        self,
        error: Exception,
        interaction: ModalInteraction,
    ) -> None:
        await interaction.edit_original_message(
            content="Oops, something went wrong."
        )


class ValorantPingImageModal(Modal):
    """modal for adding a custom image for ping alert"""

    def __init__(self) -> None:
        components: list[TextInput] = [
            TextInput(
                label="Custom Image URL",
                placeholder="url of custom image for ping alert",
                custom_id="url",
                style=TextInputStyle.short,
                max_length=100,
            ),
        ]
        super().__init__(
            title="valorant ping image",
            custom_id="valorant_ping_image",
            components=components,
        )

    async def callback(self, interaction: ModalInteraction, /) -> None:
        await interaction.response.defer()
        await interaction.edit_original_message(
            **await valorant_helper.ping_image_add(
                interaction,
                interaction.text_values["url"],
            )
        )

    async def on_error(
        self,
        error: Exception,
        interaction: ModalInteraction,
    ) -> None:
        await interaction.edit_original_message(
            content="Oops, something went wrong."
        )


class ValorantFeederMessageModal(Modal):
    """modal for adding a custom message for feeder alert"""

    def __init__(self) -> None:
        components: list[TextInput] = [
            TextInput(
                label="Custom Message",
                placeholder="custom message for feeder alert",
                custom_id="message",
                style=TextInputStyle.short,
                max_length=100,
            ),
        ]
        super().__init__(
            title="valorant feeder message",
            custom_id="valorant_feeder_message",
            components=components,
        )

    async def callback(self, interaction: ModalInteraction, /) -> None:
        await interaction.response.defer()
        await interaction.edit_original_message(
            **await valorant_helper.feeder_message_add(
                interaction,
                interaction.text_values["message"],
            )
        )

    async def on_error(
        self,
        error: Exception,
        interaction: ModalInteraction,
    ) -> None:
        await interaction.edit_original_message(
            content="Oops, something went wrong."
        )


class ValorantFeederImageModal(Modal):
    """modal for adding a custom image for feeder alert"""

    def __init__(self) -> None:
        components: list[TextInput] = [
            TextInput(
                label="Custom Image URL",
                placeholder="url of custom image for feeder alert",
                custom_id="url",
                style=TextInputStyle.short,
                max_length=100,
            ),
        ]
        super().__init__(
            title="valorant feeder image",
            custom_id="valorant_feeder_image",
            components=components,
        )

    async def callback(self, interaction: ModalInteraction, /) -> None:
        await interaction.response.defer()
        await interaction.edit_original_message(
            **await valorant_helper.feeder_image_add(
                interaction,
                interaction.text_values["url"],
            )
        )

    async def on_error(
        self,
        error: Exception,
        interaction: ModalInteraction,
    ) -> None:
        await interaction.edit_original_message(
            content="Oops, something went wrong."
        )


class ValorantStreakerMessageModal(Modal):
    """modal for adding a custom message for streaker alert"""

    def __init__(self) -> None:
        components: list[TextInput] = [
            TextInput(
                label="Custom Message",
                placeholder="custom message for streaker alert",
                custom_id="message",
                style=TextInputStyle.short,
                max_length=100,
            ),
        ]
        super().__init__(
            title="valorant streaker message",
            custom_id="valorant_streaker_message",
            components=components,
        )

    async def callback(self, interaction: ModalInteraction, /) -> None:
        await interaction.response.defer()
        await interaction.edit_original_message(
            **await valorant_helper.streaker_message_add(
                interaction,
                interaction.text_values["message"],
            )
        )

    async def on_error(
        self,
        error: Exception,
        interaction: ModalInteraction,
    ) -> None:
        await interaction.edit_original_message(
            content="Oops, something went wrong."
        )
