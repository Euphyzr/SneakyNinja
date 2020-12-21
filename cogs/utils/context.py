import discord
from discord.ext import commands

class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = self.bot.session
        self.tformat = self.bot.time_format

    def timenow(self):
        return self.bot.timenow()

    async def send_owner(self, msg, **kwargs):
        await self.bot.send_owner(msg, **kwargs)