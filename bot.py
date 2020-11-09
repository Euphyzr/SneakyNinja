import sys
import logging
import traceback
import datetime

import aiohttp
import discord
from discord.ext import commands

import config
from cogs.utils import context


logging.getLogger('discord').setLevel(logging.INFO)
log = logging.getLogger()
fmt = logging.Formatter('|{asctime}|{levelname}|{name}: {message}', '%Y-%m-%d %I:%M:%S %p', style='{')
sneakyhandler = logging.FileHandler(filename='logs/sneakyninja.log', encoding='utf-8')
sneakyhandler.addFilter(lambda rec: not rec.name.split('.')[0] == 'discord')
sneakyhandler.setFormatter(fmt)

discordhandler = logging.FileHandler(filename='logs/discord.log', mode='w', encoding='utf-8')
discordhandler.addFilter(lambda rec: rec.name.split('.')[0] == 'discord')
discordhandler.setFormatter(fmt)

log.addHandler(sneakyhandler)
log.addHandler(discordhandler)


initial_extensions = (
    'cogs.info',
    'cogs.admin',
    'cogs.mod',
    'cogs.manage',
    'cogs.fun'
)


class SneakyHelp(commands.HelpCommand):
    """SneakyNinja's help command implementation.""" 
    # really fragile help command but hey it works.

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


class SneakyNinja(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or('>>'), owner_id=config.owner_id,
            description="Greetings, I can provide various info and of course, help you run server",
            activity=discord.Activity(name='>>help', type=discord.ActivityType.listening),
            help_command=SneakyHelp(show_hidden=False, verify_checks=False, command_attrs=dict(hidden=True)),
            intents=discord.Intents(
                guilds=True, members=True, messages=True,
                voice_states=True, emojis=True, invites=True
            )
        )
        
        # utils
        self.session = None

        # preferences
        self.colour = discord.Colour(0x04f2a6)
        self.time_format = "%d %B, %Y; %I:%M %p"

        # a global cooldown mapping, to avoid command spams 
        self._global_cooldown = commands.CooldownMapping.from_cooldown(5, 6.0, commands.BucketType.member)
        self.add_check(self.global_cooldown_check)

        for extension in initial_extensions:
            try:
                self.load_extension(extension)
            except Exception as error:
                print(f'Failed to load {extension}')
                traceback.print_exception(type(error), error, error.__traceback__)


    async def on_ready(self):
        self.session = aiohttp.ClientSession(loop=self.loop)
        print(f"Logged in:\n{self.user.name} - {self.user.id}")

    async def get_context(self, message, *, cls=context.Context):
        return await super().get_context(message, cls=cls)

    async def close(self):
        await super().close()
        await self.session.close()

    async def on_command_error(self, ctx, error):
        """Global Error Handler"""

        # unwrapping commands.CommandInvokeError
        error = getattr(error, 'original', error)

        if isinstance(error, (commands.CommandNotFound, commands.CheckFailure)):
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)
        elif isinstance(error, commands.CommandOnCooldown):
            if ctx.message.author.id == ctx.bot.owner_id:
                # bot owner bypasses cooldowns
                return await ctx.reinvoke()                
            await ctx.send(error)
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(error)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(error)
        elif isinstance(error, discord.Forbidden):
            await ctx.send(error.text)
        elif isinstance(error, discord.NotFound):
            await ctx.send(error.text)
        elif isinstance(error, discord.HTTPException):
            await ctx.send(error.text)
        else:
            print('Ignoring exception in command {}:'.format(ctx.command))
            traceback.print_exception(type(error), error, error.__traceback__)

    async def global_cooldown_check(self, ctx):
        """Global Command Cooldown"""
        # this is the global cooldown implementaion
        # but cogs and commands may have their own local cooldown

        bucket = bot._global_cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(bucket, retry_after)
        return True

    def timenow(self):
        return datetime.datetime.utcnow()


bot = SneakyNinja()
bot.run(config.token)
