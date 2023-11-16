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
        self.chems_default_pools = ['all', 'complex', 'main', '10-lane', '8-lane', 'family', 'indoor']
        self.chems_pools_dict = {
            'all': ['10-Lane Pool', 'Complex Lap Pool', 'Complex Family Pool', 'Indoor Pool'],
            'all-open': ['Complex Lap Pool', 'Indoor Pool'],
            'complex': ['Complex Lap Pool', 'Complex Family Pool'],
            'main': ['10-Lane Pool', 'Indoor Pool'],
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
    async def chems(self, interaction:discord.Interaction, pool: str):
        chems = self.fred.database.select_last_chem(self.chems_pools_dict[pool])
        chems_formatted = [f'Name: <@{chem[0]}>\n Chem Check ID: {chem[1]}\n Pool: {chem[2]}\n Chlorine: {chem[3]}\t\tpH: {chem[4]}\n Temperature: {chem[5]}\n Number of Swimmers: {chem[6]}\n Time: {chem[7]}\n\n' for chem in chems]
        await interaction.response.send_message(f"__Summary of Chem Checks__:\n{''.join(chems_formatted)}", ephemeral=True)

    @discord.app_commands.command(description="vats")
    async def vats(self, interaction:discord.Interaction):
        vats = self.fred.database.select_last_vat()
        vats_formatted = [f'Guard Name: <@{vat[0]}>\n Supervisor Name: <@{vat[1]}>\n VAT ID: {vat[2]}\n Pool: {vat[3]}\n Number of Swimmers: {vat[4]}\n Number of Guards: {vat[5]}\n Stimuli: {vat[6]}\n Pass?: {vat[7]}\n Response Time (s): {vat[8]}\n Time: {vat[9]}\n\n' for vat in vats]
        await interaction.response.send_message(f"__Summary of VATs__:\n{''.join(vats_formatted)}", ephemeral=True)

async def setup(Fred):
    Fred.tree.add_command(Formstack_Commands(name="form", description="test", fred=Fred))