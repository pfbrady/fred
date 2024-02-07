import logging
from discord import Member
from discord.ext.commands import Bot
from .ymca import YMCA


log = logging.getLogger()

extensions = (
    "fred.cogs.commands2.admin.admin_commands",
    "fred.cogs.commands2.supervisor.w2w_commands",
    "fred.cogs.commands2.supervisor.formstack_commands",
    "fred.cogs.tasks2.fred_tasks"
)

class Fred(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ymca: YMCA = None     

    async def setup_hook(self) -> None:
        self.ymca = YMCA('YMCA of Delaware')

    async def on_ready(self):
        self.ymca.setup(self.guilds)
        for extension in extensions:
            try:
                await self.load_extension(extension)
            except Exception as e:
                log.exception(f"Failed to load exception {e}.")
        self.ymca.database.init_database()
        for branch in self.ymca.branches.values():
            self.ymca.database.init_database_from_branch(branch)

        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
