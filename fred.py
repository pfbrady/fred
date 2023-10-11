import settings
from discord.ext.commands import Bot
import logging
import asyncio
import cogs.tasks2.fred_tasks
import cogs.commands2.supervisor.w2w_get_commands as w2w
import database as db


class Fred(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.database = None

    async def setup_hook(self) -> None:
        # pass
        self.database = db.YMCADatabase()

    async def on_ready(self):
        await cogs.tasks2.fred_tasks.setup(self)
        await w2w.setup(self)
        self.database.init_discord_users(self.get_all_members())
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
