"""custom help command"""
from typing import List, Optional, Tuple, Union

import disnake
from disnake import Embed, Message
from disnake.ext.commands import Cog, Command, Group, HelpCommand

from views.views import PageView, SelectEmbed


class Help(HelpCommand):
    """show help commands"""

    desc_list: List[str] = [
        "A discord bot by thedylone",
        "More info on [the website](https://thedylone.github.io/laffey-bot/).",
        "[Support the bot on Ko-fi](https://ko-fi.com/thedylone)!",
        "Use `help [command]` for more info on a command.",
        "You can also use `help [category]` for more info on a category.",
    ]

    def __init__(self) -> None:
        self.description: str = "\n".join(self.desc_list)
        super().__init__()

    def get_command_signature(self, command: Command) -> str:
        return f"{command.qualified_name} {command.signature}"

    async def bot_help_embed(self, mapping) -> Embed:
        """returns the help embed for the bot"""
        home_embed = Embed(
            title="🏠 help home",
            description=self.description,
            color=0x9444B3,
        )
        for cog, commands in mapping.items():
            filtered: List[Command] = await self.filter_commands(
                commands, sort=True
            )
            command_signatures: List[str] = [
                self.get_command_signature(c) for c in filtered
            ]
            if command_signatures:
                cog_name: Optional[str] = getattr(cog, "qualified_name", None)
                if not cog_name:
                    continue
                emoji: Optional[str] = getattr(cog, "COG_EMOJI", None)
                description: Optional[str] = getattr(cog, "description", None)
                combined_name: str = (
                    emoji + " " + cog_name if emoji else cog_name
                )
                home_embed.add_field(
                    name=combined_name,
                    value=description,
                    inline=False,
                )
        return home_embed

    async def send_bot_help(self, mapping: dict) -> None:
        reply: Message = await self.context.reply("fetching help...")
        home_embed: Embed = await self.bot_help_embed(mapping)
        embeds: List[SelectEmbed] = [
            SelectEmbed(
                embed=home_embed,
                name="help",
                description="overview",
                emoji="🏠",
            )
        ]
        for cog, commands in mapping.items():
            filtered: List[Command] = await self.filter_commands(
                commands, sort=True
            )
            command_signatures: List[str] = [
                self.get_command_signature(c) for c in filtered
            ]
            if command_signatures:
                cog_name: Optional[str] = getattr(cog, "qualified_name", None)
                if not cog_name:
                    continue
                emoji: str = str(getattr(cog, "COG_EMOJI", None))
                description: Optional[str] = str(
                    getattr(cog, "description", None)
                )
                embeds.append(
                    SelectEmbed(
                        name=cog_name,
                        description=description,
                        emoji=emoji,
                        embed=await self.cog_help_embed(cog),
                    )
                )

        await reply.edit(
            content=None,
            embed=home_embed,
            view=PageView(reply=reply, embeds=embeds, reset_to_home=False),
        )

    async def cog_help_embed(self, cog: Cog) -> Embed:
        """returns the help embed for a cog"""
        embed = disnake.Embed(color=0x9444B3)
        commands: List[Command] = cog.get_commands()
        filtered: List[Command] = await self.filter_commands(
            commands, sort=True
        )
        command_signatures: List[str] = [
            self.get_command_signature(c) for c in filtered
        ]
        if command_signatures:
            cog_name: str = getattr(cog, "qualified_name", "no category")
            emoji: str = str(getattr(cog, "COG_EMOJI", None))
            description: str = str(getattr(cog, "description", None))
            combined_name: str = emoji + " " + cog_name if emoji else cog_name
            embed.title = combined_name
            embed.description = (
                description if description else self.description
            )
            for command in filtered:
                embed.add_field(
                    name=self.get_command_signature(command),
                    value=command.short_doc or "...",
                    inline=False,
                )
        return embed

    async def send_cog_help(self, cog: Cog) -> None:
        embed: Embed = await self.cog_help_embed(cog)
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: Group) -> None:
        embed = disnake.Embed(
            title=self.get_command_signature(group),
            description=self.description,
            color=0x9444B3,
        )
        embed.add_field(name="help", value=group.help)
        alias: Union[List[str], Tuple[str]] = group.aliases
        if alias:
            embed.add_field(
                name="aliases",
                value=", ".join(alias),
                inline=False,
            )

        filtered: List[Command] = await self.filter_commands(
            group.commands, sort=True
        )
        for command in filtered:
            embed.add_field(
                name=self.get_command_signature(command),
                value=command.short_doc or "...",
                inline=False,
            )

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: Command) -> None:
        embed = disnake.Embed(
            title=self.get_command_signature(command),
            description=self.description,
            color=0x9444B3,
        )
        embed.add_field(name="help", value=command.help)
        alias: Union[List[str], Tuple[str]] = command.aliases
        if alias:
            embed.add_field(
                name="aliases",
                value=", ".join(alias),
                inline=False,
            )

        await self.get_destination().send(embed=embed)

    async def send_error_message(self, error: Exception) -> None:
        embed = disnake.Embed(title="error", description=error)
        await self.get_destination().send(embed=embed)
