"""Sneaky Ninja Cogs."""

import logging

# To log in the cogs: import logging and log = logging.getLogger(__name__)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

handler = logging.FileHandler(filename='logs/sneakycogs.log', encoding='utf-8')
handler.setFormatter(logging.Formatter('|{asctime}|{levelname}|{name}: {message}', '%Y-%m-%d %I:%M:%S %p', style='{'))

log.addHandler(handler)