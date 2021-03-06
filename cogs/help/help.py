import disnake
from disnake.ext import commands

from views.views import HelpView


class Help(commands.HelpCommand):
    """show help commands"""

    def __init__(self) -> None:
        self.description = "check out more info at [the website](https://thedylone.github.io/laffey-bot/).\nUse `help [command]` for more info on a command.\nYou can also use `help [category]` for more info on a category."
        super().__init__()

    def get_command_signature(self, command):
        return f"{command.qualified_name} {command.signature}"

    async def bot_help_embed(self, mapping):
        home_embed = disnake.Embed(
            title="🏠 help home", description=self.description, color=0x9444B3
        )
        for cog, commands in mapping.items():
            filtered = await self.filter_commands(commands, sort=True)
            command_signatures = [self.get_command_signature(c) for c in filtered]
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", None)
                if not cog_name:
                    continue
                emoji = getattr(cog, "COG_EMOJI", None)
                description = getattr(cog, "description", None)
                combined_name = emoji + " " + cog_name if emoji else cog_name
                home_embed.add_field(
                    name=combined_name, value=description, inline=False
                )
        return home_embed

    async def send_bot_help(self, mapping):
        home_embed = await self.bot_help_embed(mapping)
        embeds_dict = {}
        for cog, commands in mapping.items():
            filtered = await self.filter_commands(commands, sort=True)
            command_signatures = [self.get_command_signature(c) for c in filtered]
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", None)
                if not cog_name:
                    continue
                emoji = getattr(cog, "COG_EMOJI", None)
                description = getattr(cog, "description", None)
                embeds_dict[cog_name] = {"description": description, "emoji": emoji}

        view = HelpView(self, embeds_dict)
        await self.get_destination().send(embed=home_embed, view=view)

    async def cog_help_embed(self, cog):
        embed = disnake.Embed(color=0x9444B3)
        commands = cog.get_commands()
        filtered = await self.filter_commands(commands, sort=True)
        command_signatures = [self.get_command_signature(c) for c in filtered]
        if command_signatures:
            cog_name = getattr(cog, "qualified_name", "no category")
            emoji = getattr(cog, "COG_EMOJI", None)
            description = getattr(cog, "description", None)
            combined_name = emoji + " " + cog_name if emoji else cog_name
            embed.title = combined_name
            embed.description = description if description else self.description
            for command in filtered:
                embed.add_field(
                    name=self.get_command_signature(command),
                    value=command.short_doc or "...",
                    inline=False,
                )
        return embed

    async def send_cog_help(self, cog):
        embed = await self.cog_help_embed(cog)
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group):
        embed = disnake.Embed(
            title=self.get_command_signature(group),
            description=self.description,
            color=0x9444B3,
        )
        embed.add_field(name="help", value=group.help)
        alias = group.aliases
        if alias:
            embed.add_field(name="aliases", value=", ".join(alias), inline=False)

        filtered = await self.filter_commands(group.commands, sort=True)
        for command in filtered:
            embed.add_field(
                name=self.get_command_signature(command),
                value=command.short_doc or "...",
                inline=False,
            )

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        embed = disnake.Embed(
            title=self.get_command_signature(command),
            description=self.description,
            color=0x9444B3,
        )
        embed.add_field(name="help", value=command.help)
        alias = command.aliases
        if alias:
            embed.add_field(name="aliases", value=", ".join(alias), inline=False)

        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error):
        embed = disnake.Embed(title="error", description=error)
        await self.get_destination().send(embed=embed)
