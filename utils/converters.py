import re
import argparse, shlex

import discord
from discord.ext import commands

class MemberOrFetchedUser(commands.Converter):
    async def convert(self, ctx, argument):
        """Converts to discord.Member. Tries to fetch the user if conversion fails."""
        try:
            return await commands.MemberConverter().convert(ctx, argument)
        except commands.MemberNotFound:
            if not argument.isdigit():
                raise commands.BadArgument("No member by this name, here.")
            try:
                return await ctx.bot.fetch_user(argument)
            except discord.NotFound:
                raise commands.BadArgument("This user doesn't exist.") from None


class PyCodeBlock(commands.Converter):
    async def convert(self, ctx, argument):
        """Converts a python codeblock to normal python code structure."""
        start, end = "```py\n", "```"
        if argument.startswith(start) and argument.endswith(end):
            code = argument[len(start):-len(end)]
            return code
        return argument


class Argument(argparse.ArgumentParser):
    def error(self, message):
        raise commands.BadArgument(message)

class MessageFlagParser:
    """Flag parser for message related mod commands."""

    def __init__(self, ctx, flags):
        self.ctx = ctx
        self.parser = Argument(add_help=False)
        self.predicates = []

        self._add_default_arguments()

        self.args = self.parser.parse_args(shlex.split(flags))

    @classmethod
    async def convert(cls, ctx, argument):
        return cls(ctx, argument)
        
    def _add_default_arguments(self):
        parser = self.parser

        parser.add_argument('-u', '--user', nargs='*')
        parser.add_argument('-c', '--contains', nargs='*')
        parser.add_argument('-b', '--bot', action='store_true')
        parser.add_argument('-e', '--everyone', action='store_true')
        parser.add_argument('-em', '--embed', action='store_true')
        parser.add_argument('-ro', '--reaction-over', type=int)
        parser.add_argument('-mo', '--mention-over', type=int)
        parser.add_argument('-r', '--regex')
        parser.add_argument('-ric', '--regex-ignorecase', action='store_true')


class EmbedFlagParser:
    """Flag parser for creating embed."""

    def __init__(self, ctx, flags):
        self.ctx = ctx

        self.parser = Argument(add_help=False)
        self._add_default_arguments()
        self.args = self.parser.parse_args(shlex.split(flags))

    @classmethod
    async def convert(cls, ctx, argument):
        return cls(ctx, argument)

    def _add_default_arguments(self):
        parser = self.parser

        parser.add_argument('-t', '--title')
        parser.add_argument('-d', '--description')
        parser.add_argument('-c', '--colour', nargs='+')

        parser.add_argument('-si', '--set-image')
        parser.add_argument('-st', '--set-thumbnail')
        parser.add_argument('-sf', '--set-footer', nargs=2)
        parser.add_argument('-af', '--add-field', nargs=3, action='append')
