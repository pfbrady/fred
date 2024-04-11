"""main.py module"""

from __future__ import annotations

import logging

import discord

from fred.fred import Fred
from settings import SETTINGS_DICT


def run():
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    intents = discord.Intents.all()
    intents.presences = False
    client = Fred(command_prefix='!', intents=intents)
    client.run(token=SETTINGS_DICT['discord_token'], log_handler=handler)


if __name__ == '__main__':
    run()
