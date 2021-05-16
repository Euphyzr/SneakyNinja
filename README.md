## SneakyNinja
A bot that provides with informations and helps with a few stuffs.

## Setting up
1. Clone the repo. Then setup virtual environment and install all the requirments from `requirements.txt`.
2. Create a `config.py` in the root of the directory and configure it according to the following settings:
```py
token: str = "yourbot.token.here" 
owner_ids: set[int] = {...}
prefix: str = '...' 
postgresql: str = 'postgresql://user:password@host/database' # use your db info
```
3. Setup database tables with `python3 manage.py --setup-db`.
4. Insert the cog configurations in table `cog_config` according the schemas in the cog files.