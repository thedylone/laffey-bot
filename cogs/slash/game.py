import disnake
from disnake.ext import commands


class Game(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name='jewels',
                            description='ping jewels role')
    async def ping(self, inter: disnake.ApplicationCommandInteraction):
        """pings @jewels role and sends image"""
        await inter.response.send_message("<@&943511061447987281>", file=disnake.File('jewelsignal.jpg'))


def setup(bot: commands.Bot):
    bot.add_cog(Game(bot))
