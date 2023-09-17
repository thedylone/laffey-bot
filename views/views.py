"""disnake views"""
from dataclasses import dataclass
from typing import List, Union, Optional

from disnake import (
    ApplicationCommandInteraction,
    ButtonStyle,
    Embed,
    MessageInteraction,
    SelectOption,
    InteractionMessage,
    Message,
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
        display name in dropdown
    color: Optional[int]
        embed color
    description: Optional[str]
        display description in dropdown
    emoji: Optional[str]
        display emoji in dropdown
    """

    embed: Embed
    """embed to show"""
    name: str = ""
    """display name in dropdown"""
    color: int = 0
    """embed color"""
    description: str = ""
    """display description in dropdown"""
    emoji: str = ""
    """display emoji in dropdown"""


class Menu(View):
    """menu view with buttons to navigate through pages of embeds

    upon timeout, the buttons are disabled

    attributes
    ----------
    reply: Union[InteractionMessage, Message]
        the reply message the bot sent in response to the command
    embeds: List[Embed]
        list of embeds to show
    embed_count: int
        current page number
    """

    def __init__(
        self, reply: Union[InteractionMessage, Message], embeds: List[Embed]
    ) -> None:
        """initialises the menu view with buttons and footer

        parameters
        ----------
        reply: Union[InteractionMessage, Message]
            the reply message the bot sent in response to the command
        embeds: List[Embed]
            list of embeds to show
        """
        super().__init__(timeout=300)
        self.reply: Union[InteractionMessage, Message] = reply
        """the reply message the bot sent in response to the command"""
        self.embeds: List[Embed] = embeds
        """list of embeds to show"""
        self.embed_count: int = 0
        """current page number"""

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
        """skips to the first embed

        disables the first page and previous page buttons

        parameters
        ----------
        _button: Button
            the button that was clicked
        interaction: MessageInteraction
            the interaction that triggered the button
        """
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
        """goes to the previous embed

        parameters
        ----------
        _button: Button
            the button that was clicked
        interaction: MessageInteraction
            the interaction that triggered the button
        """
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
        """goes to the next embed

        parameters
        ----------
        _button: Button
            the button that was clicked
        interaction: MessageInteraction
            the interaction that triggered the button
        """
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
        """skips to the last embed

        disables the next page and last page buttons

        parameters
        ----------
        _button: Button
            the button that was clicked
        interaction: MessageInteraction
            the interaction that triggered the button
        """
        self.embed_count = len(self.embeds) - 1
        embed: Embed = self.embeds[self.embed_count]

        self.first_page.disabled = False
        self.prev_page.disabled = False
        self.next_page.disabled = True
        self.last_page.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self) -> None:
        """disable buttons after timeout"""
        self.first_page.disabled = True
        self.prev_page.disabled = True
        self.next_page.disabled = True
        self.last_page.disabled = True
        await self.reply.edit(view=self)


class Deleter(Select):
    """select menu to delete custom messages/images

    allows the user to select multiple objects to delete

    attributes
    ----------
    guild_id: int
        the id of the guild the command was used in
    key: str
        the field in the database to delete from
    objects: List[str]
        the list of objects to delete from
    """

    def __init__(
        self,
        guild_id: int,
        key: str,
        objects: List[str],
    ) -> None:
        """initialises the deleter select menu with the objects as options

        allows the user to select multiple objects to delete

        parameters
        ----------
        guild_id: int
            the id of the guild the command was used in
        key: str
            the field in the database to delete from
        objects: List[str]
            the list of objects to delete from
        """
        self.guild_id: int = guild_id
        """the id of the guild the command was used in"""
        self.key: str = key
        """the field in the database to delete from"""
        self.objects: List[str] = objects
        """the list of objects to delete from"""

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
        await interaction.response.defer()
        for i in sorted(self.values, reverse=True):
            del self.objects[int(i)]
        # replace space in key with underscore
        key_underscore: str = self.key.replace(" ", "_")
        result: str = await db.update_guild_data(
            self.guild_id,
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
    """view for the deleter select menu

    upon timeout, the view is removed

    attributes
    ----------
    message: Union[ApplicationCommandInteraction, commands.Context]
        the message the command was used in
    reply: Union[InteractionMessage, Message]
        the reply message the bot sent in response to the command
    key: str
        the field in the database to delete from
    objects: List[str]
        the list of objects to delete from
    """

    def __init__(
        self,
        message: Union[ApplicationCommandInteraction, commands.Context],
        reply: Union[InteractionMessage, Message],
        key: str,
        objects: List[str],
    ) -> None:
        """initialises the deleter view with the select menu

        parameters
        ----------
        message: Union[ApplicationCommandInteraction, commands.Context]
            the message the command was used in
        reply: Union[InteractionMessage, Message]
            the reply message the bot sent in response to the command
        """
        super().__init__()
        if message.guild is None:
            return
        self.message: Union[
            ApplicationCommandInteraction, commands.Context
        ] = message
        """the message the command was used in"""
        self.reply: Union[InteractionMessage, Message] = reply
        """the reply message the bot sent in response to the command"""
        # Adds the dropdown to our view object.
        self.add_item(Deleter(message.guild.id, key, objects))

    async def interaction_check(self, interaction: MessageInteraction) -> bool:
        """checks if the user who sent the interaction is the same as
        the user who sent the message

        parameters
        ----------
        interaction: MessageInteraction
            the interaction that triggered the view

        returns
        -------
        bool
            whether the user who sent the interaction is the same as
            the user who sent the message
        """
        if interaction.author.id != self.message.author.id:
            await interaction.response.send_message(
                "only the user who sent this can use it!",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        await self.reply.edit(view=None)


class PageSelect(Select):
    """select menu to choose a page

    attributes
    ----------
    embeds: List[SelectEmbed]
        the list of embeds to choose from
    embeds_dict: dict[str, SelectEmbed]
        the dictionary of embeds to choose from
    current_value: str
        the current value of the select menu
    """

    def __init__(
        self,
        embeds: List[SelectEmbed],
        timeout: Optional[float] = 180.0,
        reset_to_home: bool = True,
    ) -> None:
        """initialises the page select menu with the embeds as options

        parameters
        ----------
        embeds: List[SelectEmbed]
            the list of embeds to choose from
        timeout: Optional[float]
            timeout for the view
        reset_to_home: bool
            reset_to_home for the view
        """
        self.embeds: List[SelectEmbed] = embeds
        """the list of embeds to choose from"""
        self.embeds_dict: dict[str, SelectEmbed] = {}
        """the dictionary of embeds to choose from"""
        self.current_value: str = ""
        """the current value of the select menu"""
        self._timeout: Optional[float] = timeout
        """timeout for the view"""
        self._reset_to_home: bool = reset_to_home
        """reset_to_home for the view"""

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
            embed=embed,
            view=PageView(
                embeds=self.embeds,
                reply=interaction.message,
                timeout=self._timeout,
                reset_to_home=self._reset_to_home,
            ),
        )


class PageView(View):
    """view for the page select menu

    upon timeout, the view is removed. if reset_to_home is True,
    the reply message is reset to the first embed

    attributes
    ----------
    reply: Union[InteractionMessage, Message]
        the reply message the bot sent in response to the command
    embeds: List[SelectEmbed]
        the list of embeds to choose from
    reset_to_home: bool
        whether to reset to the first embed upon timeout
    """

    def __init__(
        self,
        reply: Union[InteractionMessage, Message],
        embeds: List[SelectEmbed],
        timeout: Optional[float] = 180.0,
        reset_to_home: bool = True,
    ) -> None:
        """initialises the page view with the select menu

        parameters
        ----------
        reply: Union[InteractionMessage, Message]
            the reply message the bot sent in response to the command
        embeds: List[SelectEmbed]
            the list of embeds to choose from
        timeout: Optional[float]
            seconds until the view times out
        reset_to_home: bool
            whether to reset to the first embed upon timeout
        """
        super().__init__(timeout=timeout)
        self.reply: Union[InteractionMessage, Message] = reply
        self.embeds: List[SelectEmbed] = embeds
        self.reset_to_home: bool = reset_to_home

        self.add_item(PageSelect(embeds, timeout, reset_to_home))

    async def on_timeout(self) -> None:
        await self.reply.edit(view=None)
        if self.reset_to_home:
            await self.reply.edit(embed=self.embeds[0].embed)
