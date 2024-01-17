import logging
import settings
from discord.ext.commands import Bot
import whentowork as w2w
from .ymca.database import YMCADatabase
from .ymca import YMCA


log = logging.getLogger(__name__)

extensions = (
    "cogs.commands2.admin.admin_commands",
    "cogs.commands2.supervisor.w2w_commands",
    "cogs.commands2.supervisor.formstack_commands",
    "cogs.tasks2.fred_tasks"
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
        for branch_id, branch in self.ymca.branches.items():
            if branch.guild_id in self.guilds:
                guild = self.get_guild(branch.guild_id)
                self.ymca.database.init_discord_users(guild.members, branch_id)
                self.ymca.database.init_w2w_users(branch_id)
                self.ymca.database.init_branches(branch_id)
        self.ymca.database.load_chems()
        self.ymca.database.load_vats()

        await self.tree.sync()
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
