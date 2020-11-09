import discord
from discord.ext import commands

class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = self.bot.session
