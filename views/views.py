from __future__ import annotations
import disnake
from disnake.ext import commands


from helpers import json_helper, db_helper


class Menu(disnake.ui.View):
    def __init__(self, embeds: list[disnake.Embed]):
        super().__init__(timeout=None)
        self.embeds = embeds
        self.embed_count = 0

        self.first_page.disabled = True
        self.prev_page.disabled = True

        # Sets the footer of the embeds with their respective page numbers.
        for i, embed in enumerate(self.embeds):
            embed.set_footer(text=f"Page {i + 1} of {len(self.embeds)}")

    @disnake.ui.button(emoji="⏪", style=disnake.ButtonStyle.blurple)
    async def first_page(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        self.embed_count = 0
        embed = self.embeds[self.embed_count]
        embed.set_footer(text=f"Page 1 of {len(self.embeds)}")

        self.first_page.disabled = True
        self.prev_page.disabled = True
        self.next_page.disabled = False
        self.last_page.disabled = False
        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(emoji="◀", style=disnake.ButtonStyle.secondary)
    async def prev_page(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        self.embed_count -= 1
        embed = self.embeds[self.embed_count]

        self.next_page.disabled = False
        self.last_page.disabled = False
        if self.embed_count == 0:
            self.first_page.disabled = True
            self.prev_page.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(emoji="▶", style=disnake.ButtonStyle.secondary)
    async def next_page(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        self.embed_count += 1
        embed = self.embeds[self.embed_count]

        self.first_page.disabled = False
        self.prev_page.disabled = False
        if self.embed_count == len(self.embeds) - 1:
            self.next_page.disabled = True
            self.last_page.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

    @disnake.ui.button(emoji="⏩", style=disnake.ButtonStyle.blurple)
    async def last_page(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
        self.embed_count = len(self.embeds) - 1
        embed = self.embeds[self.embed_count]

        self.first_page.disabled = False
        self.prev_page.disabled = False
        self.next_page.disabled = True
        self.last_page.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)


class FeederMessages(disnake.ui.Select):
    def __init__(self, bot, message, feeder_messages):

        self.bot = bot
        self.message = message
        self.feeder_messages = feeder_messages

        options = [
            disnake.SelectOption(label=i, description=message)
            for i, message in enumerate(self.feeder_messages)
        ]

        super().__init__(
            placeholder="choose messages to delete...",
            min_values=1,
            max_values=len(self.feeder_messages),
            options=options,
        )

    async def callback(self, inter: disnake.MessageInteraction):
        if inter.author.id != self.message.author.id:
            await inter.response.send_message("only the user who sent this can use it!")
            return
        await inter.response.defer()
        for i in sorted(self.values, reverse=True):
            del self.feeder_messages[int(i)]
        await db_helper.update_guild_data(self.bot, self.message.guild.id, "feeder_messages", self.feeder_messages)
        await inter.edit_original_message(
            content=f"successfully deleted {len(self.values)} custom messages",
            view=None,
        )


class FeederMessagesView(disnake.ui.View):
    def __init__(self, bot, message, feeder_messages):
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(FeederMessages(bot, message, feeder_messages))


class FeederImages(disnake.ui.Select):
    def __init__(self, message):

        self.message = message
        guild_data = json_helper.load("guildData.json")
        self.feeder_images = guild_data[str(message.guild.id)]["feeder_images"]

        options = [
            disnake.SelectOption(label=i, description=image)
            for i, image in enumerate(self.feeder_images)
        ]

        super().__init__(
            placeholder="choose images to delete...",
            min_values=1,
            max_values=len(self.feeder_images),
            options=options,
        )

    async def callback(self, inter: disnake.MessageInteraction):
        if inter.author.id != self.message.author.id:
            await inter.response.send_message("only the user who sent this can use it!")
            return
        await inter.response.defer()
        guild_data = json_helper.load("guildData.json")
        for i in sorted(self.values, reverse=True):
            del self.feeder_images[int(i)]
        guild_data[str(self.message.guild.id)]["feeder_images"] = self.feeder_images
        json_helper.save(guild_data, "guildData.json")
        await inter.edit_original_message(
            content=f"successfully deleted {len(self.values)} custom images",
            view=None,
        )


class FeederImagesView(disnake.ui.View):
    def __init__(self, message):
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(FeederImages(message))
