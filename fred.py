import settings
import discord
import logging
import asyncio
<<<<<<< HEAD
=======
import sqlite3
>>>>>>> 8375c0bc6bfaa477bc8acf28fbf6892f0f2ef79d


class Fred(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.database = None

    async def setup_hook(self) -> None:
        # create the background task and run it in the background
        pass

    async def on_ready(self):
<<<<<<< HEAD
        for user in self.users:
            print(f"User ID: {user.id}, Name: {user.name}, Display: {user.display_name}")
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
=======
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
client = Fred(intents=discord.Intents.default())

con = sqlite3.connect("ymca_aquatics.db")
cur = con.cursor()
cur.execute("CREATE TABLE discord_user(id, )")

client.run(token=settings.DISCORD_TOKEN, log_handler=handler, log_level=logging.INFO)
>>>>>>> 8375c0bc6bfaa477bc8acf28fbf6892f0f2ef79d
