import settings
import discord
from discord.ext import commands, tasks
import logging
import asyncio
import cogs.fred_tasks as ft


class Fred(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.database = None

    async def setup_hook(self) -> None:
        # create the background task and run it in the background
        pass

    async def on_ready(self):
        await ft.setup(self)
        for user in self.users:
            print(f"User ID: {user.id}, Name: {user.name}, Display: {user.display_name}")
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
