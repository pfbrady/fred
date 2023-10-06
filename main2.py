import settings
import discord
import logging
import fred
import database

def run():
    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    intents=discord.Intents.default()
    intents.members = True
    client = fred.Fred(intents=intents)
    client.database = database.YMCADatabase()
    client.run(token=settings.DISCORD_TOKEN, log_handler=handler)


if __name__ == "__main__":
    run()