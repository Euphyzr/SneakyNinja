import discord
from discord.ext import commands

import textwrap
import traceback

from .utils.converters import PyCodeBlock

class Admin(commands.Cog, command_attrs=dict(hidden=True)):
    """Owner only cog for dynamic bot management."""

    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
        self._emoji = {
            'success': "\N{WHITE HEAVY CHECK MARK}",
            'failed': "\N{DOUBLE EXCLAMATION MARK}"
        }

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    async def load(self, ctx, *, extension):
        """Load an extension."""
        try:
            self.bot.load_extension(extension)
            await ctx.message.add_reaction(self._emoji['success'])
        except commands.ExtensionError as e:
            await ctx.send(e)

    @commands.command()
    async def unload(self, ctx, *, extension):
        """Unloads an extension."""
        try:
            self.bot.unload_extension(extension)
            await ctx.message.add_reaction(self._emoji['success'])
        except commands.ExtensionError as e:
            await ctx.send(e)

    @commands.command()
    async def reload(self, ctx, *, extension):
        """Reloads an extension."""
        try:
            self.bot.reload_extension(extension)
            await ctx.message.add_reaction(self._emoji['success'])
        except commands.ExtensionError as e:
            await ctx.send(e)

    @commands.command(aliases=['py'])
    async def pyrun(self, ctx, *, code: PyCodeBlock):
        """Runs a python code."""

        _globals = {
            '_': self._last_result,
            'ctx': ctx,
            'bot': self.bot,
            'author': ctx.author,
            'guild': ctx.guild,
            'channel': ctx.channel
        }
        _globals.update(globals())
        execcode = f'async def func():\n{textwrap.indent(code, "    ")}'

        iseval = False
        if len(code.split('\n')) == 1:
            try:
                compiled = compile(code, '<pyrun>', mode='eval') 
            except SyntaxError:
                compiled = compile(execcode, '<pyrun>', mode='exec')
            else:
                iseval = True
        else:
            compiled = compile(execcode, '<pyrun>', mode='exec')

        if iseval:
            try:
                value = eval(compiled, _globals)
                if value:
                    self._last_result = value
                    await ctx.send(value)
            except Exception as e:
                value = "".join(traceback.format_exception(type(e), e, e.__traceback__))
                await ctx.author.send(f"```py\n{value}```")
                await ctx.message.add_reaction(self._emoji['failed'])
            else:
                await ctx.message.add_reaction(self._emoji['success'])
            finally:
                return

        try:
            exec(compiled, _globals)
        except Exception as e:
            return await ctx.send(e)

        func = _globals['func']
        try:
            result = await func()
        except Exception as e:
            tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            await ctx.author.send(f"```py\n{tb}```")
            await ctx.message.add_reaction(self._emoji['failed'])
        else:
            if result:
                await ctx.send(result)
                self._last_result = result
            await ctx.message.add_reaction(self._emoji['success'])


def setup(bot):
    bot.add_cog(Admin(bot))
