import disnake
from disnake.ext import commands


class Game(commands.Cog, name='game-normal'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='jewels', description='ping jewels role')
    async def ping(self, ctx: commands.Context):
        """pings @jewels role and sends image"""
        await ctx.send("<@&943511061447987281>",
                       file=disnake.File('jewelsignal.jpg'))


def setup(bot: commands.Bot):
    bot.add_cog(Game(bot))
