## SneakyNinja
A bot that provides with informations and helps with a few stuffs.

## Setting up
Create a `logs/` directory and `config.py` file in the root of this directory with
the following settings:
```py
token: str = "yourbot.token.here" 
owner_ids: set[int] = {...}
prefix: str = '...' 
postgresql: str = 'postgresql://user:password@host/database' # use your db info
```
You need Python and the dependencies in `requirements.txt` to run the bot.