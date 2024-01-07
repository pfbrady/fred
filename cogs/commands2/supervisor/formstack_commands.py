import datetime
import typing
import discord
import settings
from discord.ext import commands, tasks
import w2w

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fred import Fred

class Formstack_Commands(discord.app_commands.Group):
    def __init__(self, name, description, fred):
        super().__init__(name=name, description=description)
        self.fred: Fred = fred
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

    # def is_supervisor(interaction: discord.Interaction):
    #     valid_roles = [
    #         interaction.guild.get_role(settings.SUPERVISOR_ROLE_ID),
    #         interaction.guild.get_role(settings.MEGIN_ROLE_ID)
    #     ]
    #     for role in valid_roles:
    #         if role in interaction.user.roles:
    #             return True
    #     return False

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
        interaction_branch_id = self.interaction_branch_id_from_interaction(interaction)
        chems = self.fred.database.select_last_chem(self.chems_pools_dict[pool], interaction_branch_id)
        chems_formatted = [f'Name: <@{chem[0]}>\n Chem Check ID: {chem[1]}\n Pool: {chem[2]}\n Chlorine: {chem[3]}\t\tpH: {chem[4]}\n Temperature: {chem[5]}\n Number of Swimmers: {chem[6]}\n Time: {chem[7]}\n\n' for chem in chems]
        await interaction.response.send_message(f"# Summary of Chem Checks:\n{''.join(chems_formatted)}", ephemeral=True)

    @discord.app_commands.command(description="vats")
    async def vats(self, interaction:discord.Interaction):
        interaction_branch_id = self.interaction_branch_id_from_interaction(interaction)
        vats = self.fred.database.select_last_vat(interaction_branch_id)
        vats_formatted = [f'Guard Name: <@{vat[0]}>\n Supervisor Name: <@{vat[1]}>\n VAT ID: {vat[2]}\n Pool: {vat[3]}\n Number of Swimmers: {vat[4]}\n Number of Guards: {vat[5]}\n Stimuli: {vat[6]}\n Pass?: {vat[7]}\n Response Time (s): {vat[8]}\n Time: {vat[9]}\n\n' for vat in vats]
        await interaction.response.send_message(f"# Most Recent VAT:\n{''.join(vats_formatted)}", ephemeral=True)

    #@discord.app_commands.check(is_supervisor)
    @discord.app_commands.command(description="vats")
    async def vats_dashboard(self, interaction:discord.Interaction):
        now = datetime.datetime.now()
        interaction_branch_id = self.interaction_branch_id_from_interaction(interaction)

        vats_by_guard = {}
        for guard in self.fred.database.discord_users[interaction_branch_id]:
            if interaction.guild.get_role(settings.SETTINGS_DICT['branches'][interaction_branch_id]['lifeguard_role_id']) in guard.roles:
                vats_by_guard[guard.id] = 0

        # Adding the number of VATs to each guards total
        vats = self.fred.database.select_vats_month(now, interaction_branch_id)
        for vat in vats:
            if vat[0] in vats_by_guard:
                vats_by_guard[vat[0]] += 1

        # Splitting the guards into who has and hasn't been VATed for the month
        vbg_complete = {}
        vbg_incomplete = {}
        for vat in vats_by_guard:
            if vats_by_guard.get(vat) > 0:
                vbg_complete[vat] = vats_by_guard.get(vat)
            else:
                vbg_incomplete[vat] = vats_by_guard.get(vat)

        vbg_complete = {k: v for k, v in sorted(vbg_complete.items(), key=lambda item: item[1], reverse=True)}
        vats_complete_formatted = [f'Guard: <@{vat}>: {vbg_complete.get(vat)}\n' for vat in vbg_complete]
        vats_incomplete_formatted = [f'Guard: <@{vat}>: {vbg_incomplete.get(vat)}\n' for vat in vbg_incomplete]
        await interaction.response.send_message(f"# Summary of VATs ({now.strftime('%B %Y')}):\n{''.join(vats_complete_formatted)}# --------------------\n{''.join(vats_incomplete_formatted)}", ephemeral=True)

    def interaction_branch_id_from_interaction(self, interaction: discord.Interaction):
        for branch_id, branch_info in settings.SETTINGS_DICT['branches'].items():
            if interaction.guild.id == branch_info['guild_id'] or interaction.guild.id == branch_info['test_guild_id']:
                return branch_id

async def setup(fred):
    fred.tree.add_command(Formstack_Commands(name="form", description="test", fred=fred))