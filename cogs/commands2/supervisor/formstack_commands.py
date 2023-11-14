import datetime
import typing
import discord
from discord.ext import commands, tasks
import w2w
import fred as fr

class Formstack_Commands(discord.app_commands.Group):
    def __init__(self, name, description, fred):
        super().__init__(name=name, description=description)
        self.fred: fr.Fred = fred
        self.chems_default_pools = ['all', '10-lane', '8-lane', 'family', 'indoor']
        self.chems_pools_dict = {
            'all': ['10-Lane Pool', 'Complex Lap Pool', 'Complex Family Pool', 'Indoor Pool'],
            '10-lane': ['10-Lane Pool'],
            '8-lane': ['Complex Lap Pool'],
            'family': ['Complex Family Pool'],
            'indoor': ['Indoor Pool']
        }

    async def chems_pool_auto(self, interaction: discord.Interaction, current: str
    )-> typing.List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=default_pos, value=default_pos) 
            for default_pos in self.chems_default_pools if current.lower() in default_pos.lower()
        ]

    @discord.app_commands.command(description="chems")
    @discord.app_commands.describe(pool="Specific pool location. Options are listed above.")
    @discord.app_commands.autocomplete(pool=chems_pool_auto)
    async def guards(self, interaction:discord.Interaction, pool: str):
        chems = self.fred.database.select_last_chem(pool=self.chems_pools_dict[pool])
        await interaction.response.send_message(f"Notification: {' '.join(chems)}.")

async def setup(Fred):
    Fred.tree.add_command(Formstack_Commands(name="form", description="test", fred=Fred))