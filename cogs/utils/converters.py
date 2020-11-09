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
        
    def add_argument(self, *args, **kwargs):
        self.parse.add_argument(*args, *kwargs)

    def add_predicate(self, pred):
        self.predicates.append(pred)

    async def get_predicate(self):
        await self._set_default_predicate()
        return self.predicates

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

    async def _set_default_predicate(self):
        args = self.args
        ctx = self.ctx

        if args.user:
            user = [await MemberOrFetchedUser().convert(ctx, user) for user in args.user]
            self.predicates.append(lambda m: m.author in user)
        if args.contains:
            self.predicates.append(lambda m: any(contain in m.content for contain in args.contains))
        if args.bot:
            self.predicates.append(lambda m: m.author.bot)
        if args.everyone:
            self.predicates.append(lambda m: m.mention_everyone)
        if args.embed:
            self.predicates.append(lambda m: bool(m.embeds))
        if args.reaction_over:
            self.predicates.append(lambda m: len(m.reactions) > args.reaction_over)
        if args.mention_over:
            self.predicates.append(lambda m: len(m.raw_mentions) > args.mention_over)
        if args.regex:
            if args.regex_ignorecase:
                pattern = re.compile(args.regex, re.IGNORECASE)
            else:
                pattern = re.compile(args.regex)

            self.predicates.append(lambda m: bool(pattern.search(m.content)))


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
