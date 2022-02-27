import disnake
import random
from disnake.ext import commands


class General(commands.Cog, name='general'):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ping", description="get bot's latency")
    async def ping(self, ctx: commands.Context):
        """get the bot's current websocket latency."""
        await ctx.send(f"pong! {round(self.bot.latency * 1000)}ms")
        
    @commands.command(name="flip", description="flip a coin and show the result")
    async def ping(self, ctx: commands.Context):
        """flips a coin kekg"""
        results = ["Heads!","Tails!"]
        await ctx.send(f"<@{ctx.author.id}> You got... {random.choice(results)}")


def setup(bot: commands.Bot):
    bot.add_cog(General(bot))
