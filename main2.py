import settings
import discord
import logging
from fred import Fred
import database

def run():
    handler = logging.FileHandler(filename=f'discord.log', encoding='utf-8', mode='w')
    intents=discord.Intents.all()
    intents.presences = False
    async with Fred(intents=intents) as bot:
        await bot.run
    client = Fred(command_prefix='!', intents=intents)
    client.run(token=settings.DISCORD_TOKEN, log_handler=handler)


if __name__ == "__main__":
    run()