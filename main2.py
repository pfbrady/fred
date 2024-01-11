import logging
import settings
import discord
from fred.fred import Fred

def run():
    handler = logging.FileHandler(filename=f'discord.log', encoding='utf-8', mode='w')
    intents=discord.Intents.all()
    intents.presences = False
    client = Fred(command_prefix='!', intents=intents,)
    client.run(token=settings.SETTINGS_DICT['discord_token'], log_handler=handler)


if __name__ == "__main__":
    run()