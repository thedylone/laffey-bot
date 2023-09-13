"""disnake modals"""

from disnake import ModalInteraction, TextInputStyle
from disnake.ui import Modal, TextInput

from helpers import valorant


class ValorantWatchModal(Modal):
    """adds a player to the database via `valorant watch`"""

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
            **await valorant.watch(
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
    """adds a custom image for `valorant ping`"""

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
            **await valorant.ping_image_add(
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


class FeederMessageModal(Modal):
    """adds a custom feeder alert message for the guild"""

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
            **await valorant.feeder_message_add(
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


class FeederImageModal(Modal):
    """adds a custom feeder alert image for the guild"""

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
            **await valorant.feeder_image_add(
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


class StreakerMessageModal(Modal):
    """adds a custom streaker alert message for the guild"""

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
            **await valorant.streaker_message_add(
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
