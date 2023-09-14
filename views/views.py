"""disnake views"""
from dataclasses import dataclass
from typing import List, Union

from disnake import (
    ApplicationCommandInteraction,
    ButtonStyle,
    Embed,
    MessageInteraction,
    SelectOption,
)
from disnake.ext import commands
from disnake.ui import Button, Select, View, button

from helpers.db import db


@dataclass
class SelectEmbed:
    """stores information about an embed for the select menu

    parameters
    ----------
    embed: Embed
        embed to show
    name: Optional[str]
        name of the embed
    color: Optional[int]
        color of the embed
    description: Optional[str]
        description of the embed
    emoji: Optional[str]
        emoji of the embed
    """

    embed: Embed
    name: str = ""
    color: int = 0
    description: str = ""
    emoji: str = ""


class Menu(View):
    """menu view with buttons to navigate through pages"""

    def __init__(self, embeds: List[Embed]) -> None:
        super().__init__(timeout=300)
        self.embeds: List[Embed] = embeds
        self.embed_count: int = 0

        self.first_page.disabled = True
        self.prev_page.disabled = True

        # Sets the footer of the embeds with their respective page numbers.
        for i, embed in enumerate(self.embeds):
            embed.set_footer(text=f"Page {i + 1} of {len(self.embeds)}")

    @button(emoji="⏪", style=ButtonStyle.blurple)
    async def first_page(
        self,
        _button: Button,
        interaction: MessageInteraction,
    ) -> None:
        """go to first page"""
        self.embed_count = 0
        embed: Embed = self.embeds[self.embed_count]
        embed.set_footer(text=f"Page 1 of {len(self.embeds)}")

        self.first_page.disabled = True
        self.prev_page.disabled = True
        self.next_page.disabled = False
        self.last_page.disabled = False
        await interaction.response.edit_message(embed=embed, view=self)

    @button(emoji="◀", style=ButtonStyle.secondary)
    async def prev_page(
        self,
        _button: Button,
        interaction: MessageInteraction,
    ) -> None:
        """go to previous page"""
        self.embed_count -= 1
        embed: Embed = self.embeds[self.embed_count]

        self.next_page.disabled = False
        self.last_page.disabled = False
        if self.embed_count == 0:
            self.first_page.disabled = True
            self.prev_page.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

    @button(emoji="▶", style=ButtonStyle.secondary)
    async def next_page(
        self,
        _button: Button,
        interaction: MessageInteraction,
    ) -> None:
        """go to next page"""
        self.embed_count += 1
        embed: Embed = self.embeds[self.embed_count]

        self.first_page.disabled = False
        self.prev_page.disabled = False
        if self.embed_count == len(self.embeds) - 1:
            self.next_page.disabled = True
            self.last_page.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

    @button(emoji="⏩", style=ButtonStyle.blurple)
    async def last_page(
        self,
        _button: Button,
        interaction: MessageInteraction,
    ) -> None:
        """go to last page"""
        self.embed_count = len(self.embeds) - 1
        embed: Embed = self.embeds[self.embed_count]

        self.first_page.disabled = False
        self.prev_page.disabled = False
        self.next_page.disabled = True
        self.last_page.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)


class Deleter(Select):
    """select menu to delete custom messages/images"""

    def __init__(
        self,
        message: Union[ApplicationCommandInteraction, commands.Context],
        key: str,
        objects: List[str],
    ) -> None:
        self.message: Union[
            ApplicationCommandInteraction, commands.Context
        ] = message
        self.key: str = key
        self.objects: List[str] = objects

        options: List[SelectOption] = [
            SelectOption(label=str(i), description=obj)
            for i, obj in enumerate(objects)
        ]

        super().__init__(
            placeholder=f"choose {key} to delete...",
            min_values=1,
            max_values=len(self.objects),
            options=options,
        )

    async def callback(self, interaction: MessageInteraction, /) -> None:
        if interaction.author.id != self.message.author.id:
            await interaction.response.send_message(
                "only the user who sent this can use it!",
                ephemeral=True,
            )
            return
        await interaction.response.defer()
        if self.message.guild is None:
            await interaction.edit_original_message(
                content="this command can only be used in a server",
            )
            return
        for i in sorted(self.values, reverse=True):
            del self.objects[int(i)]
        # replace space in key with underscore
        key_underscore: str = self.key.replace(" ", "_")
        result: str = await db.update_guild_data(
            self.message.guild.id,
            **{key_underscore: self.objects},
        )
        if result.startswith("UPDATE"):
            await interaction.edit_original_message(
                content=f"successfully deleted {len(self.values)} {self.key}",
                view=None,
            )
        else:
            await interaction.edit_original_message(
                content="something went wrong",
                view=None,
            )


class DeleterView(View):
    """view for the deleter select menu"""

    def __init__(
        self,
        message: Union[ApplicationCommandInteraction, commands.Context],
        key: str,
        objects: List[str],
    ) -> None:
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(Deleter(message, key, objects))


class PageSelect(Select):
    """select menu to choose a page"""

    def __init__(self, embeds: List[SelectEmbed]) -> None:
        self.embeds: List[SelectEmbed] = embeds
        self.embeds_dict: dict[str, SelectEmbed] = {}
        self.current_value: str = ""

        options: List[SelectOption] = []
        for embed in embeds:
            options.append(
                SelectOption(
                    label=embed.name,
                    description=embed.description,
                    emoji=embed.emoji,
                )
            )
            self.embeds_dict[embed.name] = embed

        super().__init__(
            placeholder="choose category to show...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: MessageInteraction, /) -> None:
        if self.current_value == self.values[0]:
            return
        self.current_value = self.values[0]
        embed: Embed = self.embeds_dict[self.values[0]].embed
        await interaction.response.edit_message(
            embed=embed, view=PageView(self.embeds)
        )


class PageView(View):
    """view for the page select menu"""

    def __init__(self, embeds: List[SelectEmbed]) -> None:
        super().__init__(timeout=600)

        self.add_item(PageSelect(embeds))
