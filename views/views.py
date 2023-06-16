"""disnake views"""

from disnake import (
    Embed,
    MessageInteraction,
    ApplicationCommandInteraction,
    ButtonStyle,
    SelectOption,
)
from disnake.ext import commands
from disnake.ui import View, Select, button, Button

from helpers import db_helper


class SelectEmbed:
    """class to store information about an embed for the select menu"""

    def __init__(
        self,
        embed: Embed,
        name: str = "",
        color: int = 0,
        description: str = "",
        emoji: str = "",
    ) -> None:
        self.embed: Embed = embed
        self.name: str = name
        self.color: int = color
        self.description: str = description
        self.emoji: str = emoji


class Menu(View):
    """class to create a menu"""

    def __init__(self, embeds: list[Embed]) -> None:
        super().__init__(timeout=None)
        self.embeds: list[Embed] = embeds
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
    """class to create a select menu to delete custom messages/images"""

    def __init__(
        self,
        bot: commands.Bot,
        message: ApplicationCommandInteraction | commands.Context,
        key: str,
        objects: list[str],
    ) -> None:
        self.bot: commands.Bot = bot
        self.message: ApplicationCommandInteraction | commands.Context = (
            message
        )
        self.key: str = key
        self.objects: list[str] = objects

        options: list[SelectOption] = [
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
        result: str = await db_helper.update_guild_data(
            self.bot,
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
    """class to create a view for the deleter select menu"""

    def __init__(
        self,
        bot: commands.Bot,
        message: ApplicationCommandInteraction | commands.Context,
        key: str,
        objects: list[str],
    ) -> None:
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(Deleter(bot, message, key, objects))


class PageSelect(Select):
    """class to create a select menu to choose a page"""

    def __init__(self, embeds: list[SelectEmbed]) -> None:

        self.embeds: list[SelectEmbed] = embeds
        self.embeds_dict: dict[str, SelectEmbed] = {}
        self.current_value: str = ""

        options: list[SelectOption] = []
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
    """class to create a view for the page select menu"""

    def __init__(self, embeds: list[SelectEmbed]) -> None:
        super().__init__()

        self.add_item(PageSelect(embeds))
