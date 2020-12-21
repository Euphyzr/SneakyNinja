import discord
from discord.ext import commands

import traceback


class SneakyHelp(commands.HelpCommand):
    """SneakyNinja's help command implementation.""" 

    def get_ending_note(self):
        return (
            "Use {0}{1} [command] for more info on a command. For more info on a "
            "category, use {0}{1} [category].".format(self.clean_prefix, self.invoked_with)
        )
    
    def get_sneaky_command_signature(self, command):
        return '{0.qualified_name} {0.signature}'.format(command)

    async def send_bot_help(self, mapping):
        ctx = self.context
        em = discord.Embed(title='Sneaky Help', colour=ctx.bot.colour)

        description = ctx.bot.description
        if description:
            em.description = description

        for cog, commands in mapping.items():
            name = 'No Category' if cog is None else cog.qualified_name
            filteredcmds = await self.filter_commands(commands, sort=True)
            if filteredcmds:
                value = ', '.join(f"*`{cmd.name}`*" for cmd in filteredcmds)
                
                em.add_field(name=name, value=value)
        em.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=em)

    async def send_cog_help(self, cog):
        em = discord.Embed(title=cog.qualified_name, colour=self.context.bot.colour)
        if cog.description:
            em.description = cog.description

        filteredcmds = await self.filter_commands(cog.get_commands(), sort=True)
        for cmd in filteredcmds:
            doc = f'*`{cmd.short_doc}`*' if cmd.short_doc else '`...`'
            em.add_field(name=self.get_sneaky_command_signature(cmd), value=doc)

        em.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=em)

    async def send_group_help(self, group):
        em = discord.Embed(title=group.qualified_name, colour=self.context.bot.colour)
        if group.help:
            em.description = group.help
        
        filteredcmds = await self.filter_commands(group.commands, sort=True)
        if filteredcmds:
            for cmd in filteredcmds:
                doc = f'*`{cmd.short_doc}`*' if cmd.short_doc else '`...`'
                em.add_field(name=self.get_sneaky_command_signature(cmd), value=doc)

        em.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=em)

    async def send_command_help(self, command):
        em = discord.Embed(title=command.qualified_name, colour=self.context.bot.colour)
        em.add_field(name='usage', value=self.get_command_signature(command))
        if command.short_doc:
            em.description = command.short_doc
            commandhelp = command.help[len(command.short_doc):]
            if commandhelp:
                em.add_field(name='help', value=commandhelp, inline=False)

        em.set_footer(text=self.get_ending_note())
        await self.get_destination().send(embed=em)


class SneakyCore(commands.Cog):
    """Second layer of core bot behavior.
    
    This cog is reponsible for:-
        1. Custom HelpCommand
        2. Error Handling
    """

    def __init__(self, bot):
        self.bot = bot
        bot.help_command = SneakyHelp(show_hidden=False, verify_checks=False, command_attrs={'hidden': True})
        bot.help_command.cog = self

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Global Error Handler"""

        # unwrapping commands.CommandInvokeError
        error = getattr(error, 'original', error)
        ignored_errs = (commands.CommandNotFound, commands.CheckFailure)
        send_errs = (commands.BadArgument, commands.MissingPermissions, discord.NotFound,
                    discord.Forbidden, discord.HTTPException, commands.MissingRequiredArgument)

        if isinstance(error, ignored_errs):
            return
        if isinstance(error, commands.CommandOnCooldown):
            if ctx.message.author.id == ctx.bot.owner_id:
                # bot owner bypasses cooldowns
                return await ctx.reinvoke()                
            await ctx.send(error)
        elif isinstance(error, send_errs):
            error = getattr(error, 'text', error)
            await ctx.send(error)
        else:
            print(f"Ignoring exception in command {ctx.command}:")
            traceback.print_exception(type(error), error, error.__traceback__)


def setup(bot):
    bot.add_cog(SneakyCore(bot))
