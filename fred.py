import settings
import discord
from discord.ext import commands, tasks
import logging
import asyncio
import cogs.fred_tasks as ft
import database as db


class Fred(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.database = None

    async def setup_hook(self) -> None:
        # pass
        self.database = db.YMCADatabase()

    async def on_ready(self):
        await ft.setup(self)
        self.database.init_discord_users(self.get_all_members())
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
