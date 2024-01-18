import logging
from discord.ext.commands import Bot
from .ymca import YMCA


log = logging.getLogger(__name__)

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

        for extension in extensions:
            try:
                await self.load_extension(extension)
            except Exception as e:
                log.exception(f"Failed to load exception {e}.")

    async def on_ready(self):
        for branch in self.ymca.branches.values():
            for guild in self.guilds:
                if branch.guild_id == guild.id:
                    branch.guild = guild
                elif branch.test_guild_id == guild.id:
                    branch.test_guild = guild

        self.ymca.database.init_database()
        for branch in self.ymca.branches.values():
            self.ymca.database.init_database_from_branch(branch)

        await self.tree.sync()
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
