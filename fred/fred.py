import logging
import settings
from discord.ext.commands import Bot
import whentowork as w2w
from .database import YMCADatabase
from .ymca import YMCA


log = logging.getLogger(__name__)

extensions = (
    "cogs.commands2.supervisor.w2w_commands",
    "cogs.commands2.supervisor.formstack_commands",
    "cogs.tasks2.fred_tasks"
)

class Fred(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ymca: YMCA = None
        self.database: YMCADatabase = None
        

    async def setup_hook(self) -> None:
        self.ymca = YMCA('YMCA of Delaware')
        self.database = YMCADatabase()

        for extension in extensions:
            try:
                await self.load_extension(extension)
            except Exception as e:
                log.exception(f"Failed to load exception {e}.")

    async def on_ready(self):
        for guild in self.guilds:
            for branch_id, branch_info in settings.SETTINGS_DICT['branches'].items():
                if branch_info['guild_id'] == guild.id:
                    self.database.init_discord_users(self.get_all_members(), branch_id)
                    self.database.init_w2w_users(branch_id)
        self.database.load_chems()
        self.database.load_vats()

        await self.tree.sync()

        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
