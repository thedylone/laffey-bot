import disnake
from disnake.ext import commands

from views.views import HelpView


class Help(commands.HelpCommand):
    def __init__(self) -> None:
        self.description = "check out more info at [the website](https://thedylone.github.io/laffey-bot/).\nUse `help [command]` for more info on a command.\nYou can also use `help [category]` for more info on a category."
        super().__init__()

    def get_command_signature(self, command):
        return f"{command.qualified_name} {command.signature}"

    async def send_bot_help(self, mapping):
        channel = self.get_destination()
        embeds = []
        cognames = []
        for cog, commands in mapping.items():
            embed = disnake.Embed(title="help", description=self.description)
            filtered = await self.filter_commands(commands, sort=True)
            command_signatures = [self.get_command_signature(c) for c in filtered]
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "no category")
                cognames.append(cog_name)
                embed.add_field(
                    name=cog_name, value="\n".join(command_signatures), inline=False
                )
                embeds.append(embed)
        view = HelpView(embeds, cognames) if len(embeds) > 1 else None
        await channel.send(embed=embeds[0], view=view)

    async def send_cog_help(self, cog):
        channel = self.get_destination()
        embed = disnake.Embed(title="help", description=self.description)
        commands = cog.get_commands()
        filtered = await self.filter_commands(commands, sort=True)
        command_signatures = [self.get_command_signature(c) for c in filtered]
        if command_signatures:
            cog_name = getattr(cog, "qualified_name", "no category")
            embed.add_field(
                name=cog_name, value="\n".join(command_signatures), inline=False
            )
        await channel.send(embed=embed)

    async def send_group_help(self, group):
        destination = self.get_destination()
        return await destination.send(group)

    async def send_command_help(self, command):
        embed = disnake.Embed(
            title=self.get_command_signature(command), description=self.description
        )
        embed.add_field(name="help", value=command.help)
        alias = command.aliases
        if alias:
            embed.add_field(name="aliases", value=", ".join(alias), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_error_message(self, error):
        embed = disnake.Embed(title="error", description=error)
        channel = self.get_destination()
        await channel.send(embed=embed)
