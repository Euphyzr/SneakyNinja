import asyncio
import config


async def sql_setup():
    import asyncpg

    SCHEMAS = [
        """CREATE TABLE IF NOT EXISTS cog_config(
            id serial NOT NULL PRIMARY KEY, name text NOT NULL UNIQUE, data jsonb NOT NULL
        );""",
    ]
    conn = await asyncpg.connect(config.postgresql)
    async with conn.transaction():
        for schema in SCHEMAS:
            # asyncio.create_task (in background) => can't perform operation while another's in progress
            # asyncio.gather => RuntimeError: task got bad yield
            await conn.execute(schema)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Utility commands for sneakyninja management.')
    parser.add_argument('--setup-db', action='store_true', help='Setup SQL tables')

    args = parser.parse_args()
    # asyncio.run => 'RuntimeError: Event loop is closed'
    async_run = asyncio.get_event_loop().run_until_complete
    
    if args.setup_db:
        async_run(sql_setup())
    else:
        parser.print_help()