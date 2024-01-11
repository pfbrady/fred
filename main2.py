import logging
import settings
import discord
from fred import Fred
import database
import whentowork

def run():
    handler = logging.FileHandler(filename=f'discord.log', encoding='utf-8', mode='w')
    intents=discord.Intents.all()
    intents.presences = False
    client = Fred(command_prefix='!', intents=intents)
    client.run(token=settings.DISCORD_TOKEN, log_handler=handler)


if __name__ == "__main__":
    run()