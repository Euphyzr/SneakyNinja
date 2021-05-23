import discord
from discord.ext import commands, tasks

import datetime

from utils.misc import get_ordinal

# Config Schema
# -------------
# config = {
#     'should_run': False,
#     'message_id': None,
#     'channel_id': None,
#     'ROUTINE': [[... , ... , ...],  # monday
#                 [... , ... , ...] ,
#                 [... , ... , ...],
#                 [... , ... , ...],
#                 [... , ... , ...],
#                 [... , ... , ...],
#                 [... , ... , ...]],  # sunday
#     'LINKS'  : {'key': 'link', ...}  # key should correspond to the names in ROUTINE
# }

class School(commands.Cog):
    """Commands for my class's discord server."""

    def __init__(self, bot):
        self.bot = bot
        self._message = None
        self.config = {}
        self.set_routine.start()

    def cog_unload(self):
        self.set_routine.cancel()

    async def cog_check(self, ctx):
        return ctx.guild and ctx.guild.id == 761601641182920752

    async def cog_command_error(self, ctx, error):
        if type(error) == commands.CheckFailure:
            await ctx.send('This command is unavailable for this guild.')

    async def load_config(self):
        async with self.bot.pool.acquire() as conn:
            self.config = await conn.fetchval("""SELECT data FROM cog_config WHERE name='school'""")

    async def update_dbconfig(self, conf=None):
        async with self.bot.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO cog_config(name, data) VALUES('school', $1)
                ON CONFLICT (name) DO UPDATE SET data = $1""", conf or self.config
            )

    async def _set_config(self, *, channel_id, message_id):
        if not self.config:
            await self.load_config()
        self.config['should_run'] = True
        self.config['message_id'] = message_id
        self.config['channel_id'] = channel_id
        await self.update_dbconfig()

    @tasks.loop(hours=6)
    async def set_routine(self):
        await self._message.edit(content=None, embed=await self._make_routine_embed(self._message.guild))

    @set_routine.before_loop
    async def on_routine_start(self):
        await self.bot.wait_until_ready()

        if not self.config:
            await self.load_config()
            if self.config is None:
                raise RuntimeError(f"No config found for {__name__}")

        if not self.config['should_run']:
            # routine tracking wasn't initiated by the user
            return self.set_routine.cancel()

        if not self._message:
            # tracking was initialed by user. So, starting again on bot restart.
            channel = await self.bot.fetch_channel(self.config['channel_id'])
            self._message = await channel.fetch_message(self.config['message_id'])
    
    @set_routine.after_loop
    async def on_routine_cancel(self):
        if self._message:
            await self._message.edit(content='Auto-updating cancelled. `Bot offline/Cog unloaded`')

    async def _make_routine_embed(self, guild):
        today   = datetime.date.today()
        ROUTINE = self.config.get('ROUTINE')
        LINKS   = self.config.get('LINKS')
        periods = ROUTINE[today.weekday()]
        
        em = discord.Embed(
            title=f'Class Routine [{today.strftime("%A")}]',
            colour=self.bot.colour,
            description='This is an auto-updating daily routine. Click on the names to join the meeting!',
            timestamp=self.bot.timenow(),
        )
        em.set_author(
            name=guild.name,
            icon_url=guild.icon_url,
        )
        creator = guild.get_member(self.bot.creator_id) or self.bot.get_user(self.bot.creator_id)
        em.set_footer(
            text=f'Made with \U00002764 by {creator.display_name} | updated',
            icon_url=creator.avatar_url,
        )
        for index, period in enumerate(periods):
            ordinal_period = get_ordinal(index + 1)
            em.add_field(name=f'{ordinal_period} Period', value=f'[{period}]({LINKS.get(period)})')

        return em

    @commands.group(invoke_without_command=True)
    async def routine(self, ctx):
        """An auto updating daily routine of my class."""
        pass

    @routine.command(name='start')
    async def routine_start(self, ctx):
        """Start the routine."""
        if self.set_routine.is_running():
            return await ctx.send(f"It's already running at:\n{self._message.jump_url}")

        self._message = await ctx.send("Starting...")
        await self._set_config(channel_id=ctx.channel.id, message_id=self._message.id)
        self.set_routine.start()

    @routine.command(name='cancel')
    async def routine_cancel(self, ctx):
        """Cancel the routine."""
        # we don't want the after_loop coro to run when cancelling through the command
        _coro = self.set_routine._after_loop
        self.set_routine._after_loop = None
        self.set_routine.cancel()

        self.config['should_run'] = False
        await self.update_dbconfig()
        if self._message:
            await self._message.edit(content='Routine Cancelled.', embed=None)

        self.set_routine._after_loop = _coro

    @routine.command(name='restart')
    async def routine_restart(self, ctx):
        """Restart the routine."""
        self.set_routine.restart()
        await ctx.send("Restarted the routine.")

def setup(bot):
    bot.add_cog(School(bot))