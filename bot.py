import datetime
import traceback

import aiohttp
import discord
from discord.ext import commands

import config
from utils import context

initial_extensions = (
    'cogs.info',
    'cogs.admin',
    'cogs.mod',
    'cogs.manage',
    'cogs.fun',
    'cogs.school',
    'cogs.utilities',
)

class SneakyNinja(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(config.prefix), owner_ids=config.owner_ids,
            description="Greetings, I can provide various info and of course, help you run server",
            activity=discord.Activity(name=f'{config.prefix}help', type=discord.ActivityType.listening),
            intents=discord.Intents(
                guilds=True, members=True, messages=True,
                voice_states=True, emojis=True, invites=True
            )
        )
        
        # utils
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.webhook = discord.Webhook.from_url(
            config.webhook_url,
            adapter=discord.AsyncWebhookAdapter(session=self.session)
        )

        # preferences
        self.creator_id = 411506718187716610
        self.colour = discord.Colour(0x04f2a6)
        self.time_format = "%d %B, %Y; %I:%M %p"

        # a global cooldown mapping, to avoid command spams 
        self._global_cooldown = commands.CooldownMapping.from_cooldown(5, 6.0, commands.BucketType.member)
        self.add_check(self.global_cooldown_check)

        self.load_extension('cogs.core')  # cogs.core's exception shouldn't be ignored
        for extension in initial_extensions:
            try:
                self.load_extension(extension)
            except Exception as error:
                print(f'Failed to load {extension}')
                traceback.print_exception(type(error), error, error.__traceback__)


    async def on_ready(self):
        print(f"Logged in:\n{self.user.name} - {self.user.id}")

    async def get_context(self, message, *, cls=context.Context):
        return await super().get_context(message, cls=cls)

    async def close(self):
        await super().close()
        await self.session.close()
        await self.pool.close()

    async def global_cooldown_check(self, ctx):
        """Global Command Cooldown"""

        # this is the global cooldown implementaion
        # but cogs and commands may have their own local cooldown
        bucket = self._global_cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(bucket, retry_after)
        return True

    def timenow(self):
        return datetime.datetime.utcnow()

    async def send_owner(self, msg, **kwargs):
        for owner_id in self.owner_ids:
            owner = self.get_user(owner_id) or self.fetch_user(owner_id)
            await owner.send(msg, **kwargs)

    async def webhook_log(self, *args, **kwargs):
        avatar_url = kwargs.pop('avatar_url', self.user.avatar_url)
        username = kwargs.pop('username', str(self.user.name)) + kwargs.pop('username_plus', '')

        await self.webhook.send(*args, **kwargs, username=username, avatar_url=avatar_url)

if __name__ == '__main__':
    import asyncio
    import asyncpg
    import logging
    import json
    from pathlib import Path

    p = Path('.') / 'logs'
    if not p.exists():
        p.mkdir()

    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.DEBUG)
    discord_handler = logging.FileHandler(filename='logs/discord.log', encoding='utf-8', mode='w')
    discord_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    discord_logger.addHandler(discord_handler)

    async def init(conn):
        await conn.set_type_codec('jsonb', encoder=json.dumps, decoder=json.loads, schema='pg_catalog', format='text')
    loop = asyncio.get_event_loop()
    pool = loop.run_until_complete(asyncpg.create_pool(config.postgresql, init=init))

    bot = SneakyNinja()
    bot.pool = pool
    bot.run(config.token)