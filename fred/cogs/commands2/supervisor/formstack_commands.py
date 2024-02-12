from __future__ import annotations

import datetime
import discord
import settings
from discord.ext import commands, tasks
import fred.w2w as w2w

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fred.fred import Fred
    from fred import ChemCheck, Branch
    from typing import List

class Formstack_Commands(discord.app_commands.Group):
    def __init__(self, name, description, fred: Fred):
        super().__init__(name=name, description=description)
        self.fred: Fred = fred

    async def chems_pool_auto(self, interaction: discord.Interaction, current: str
    )-> List[discord.app_commands.Choice[str]]:
        chems_default_pools = ['all']
        int_branch = self.fred.ymca.get_branch_by_guild_id(interaction.guild_id)
        for pool_group in int_branch.pool_groups:
            chems_default_pools.append(pool_group.name.replace(' ', '-').lower())
            for pool in pool_group.pools:
                chems_default_pools.append(pool.name.replace(' ', '-').lower())
        return [
            discord.app_commands.Choice(name=default_pos, value=default_pos) 
            for default_pos in chems_default_pools if current.lower() in default_pos.lower()
        ]

    @discord.app_commands.command(description="Summary of chemical checks for the indicated pools")
    @discord.app_commands.describe(pool="Specific pool location. Options are listed above")
    @discord.app_commands.autocomplete(pool=chems_pool_auto)
    async def chems(self, interaction:discord.Interaction, pool: str):
        int_branch = self.fred.ymca.get_branch_by_guild_id(interaction.guild_id)
        selected_chems: List[ChemCheck] = []
        for pool_group in int_branch.pool_groups:
            if pool in pool_group.aliases:
                selected_chems.extend(self.fred.ymca.database.select_last_chems(int_branch, pool_group.pools))
                continue
            for pool_obj in pool_group.pools:
                if pool in pool_obj.aliases or pool =='all':
                    selected_chems.append(self.fred.ymca.database.select_last_chem(int_branch, pool_obj))

        chems_formatted = []
        for chem in selected_chems:
            pool = int_branch.get_pool_by_pool_id(chem.pool_id)
            pool_name = pool.name if pool else 'Pool Name Error'
            chems_formatted.append(f'Name: <@{chem.discord_id}>\n Chem Check ID: {chem.chem_uuid}\n Pool: {pool_name}\n Chlorine: {chem.chlorine}\t\tpH: {chem.ph}\n Temperature: {chem.water_temp}\n Number of Swimmers: {chem.num_of_swimmers}\n Time: {chem.sample_time}\n\n')
        await interaction.response.send_message(f"# Summary of Chem Checks:\n{''.join(chems_formatted)}", ephemeral=True)

    async def vats_pool_auto(self, interaction: discord.Interaction, current: str
    )-> List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=default_pos, value=default_pos) 
            for default_pos in ['last', 'guard-dashboard', 'sup-dashboard'] if current.lower() in default_pos.lower()
        ]

    @discord.app_commands.command(description="Summary of VAT information")
    @discord.app_commands.autocomplete(group=vats_pool_auto)
    async def vats(self, interaction:discord.Interaction, group: str):
        int_branch = self.fred.ymca.get_branch_by_guild_id(interaction.guild_id)
        if group == 'last':
            vat = self.fred.ymca.database.select_last_vat(int_branch)
            pool = int_branch.get_pool_by_pool_id(vat.pool_id)
            pool_name = pool.name if pool else 'Pool Name Error'
            vat_formatted = f'Guard Name: <@{vat.guard_discord_id}>\n Supervisor Name: <@{vat.sup_discord_id}>\n VAT ID: {vat.vat_uuid}\n Pool: {pool_name}\n Number of Swimmers: {vat.num_of_swimmers}\n Number of Guards: {vat.num_of_guards}\n Stimuli: {vat.stimuli}\n Pass?: {vat.vat_pass}\n Response Time (s): {vat.response_time}\n Time: {vat.vat_time}\n\n'
            await interaction.response.send_message(f"# Most Recent VAT:\n{vat_formatted}", ephemeral=True)
        elif group == 'guard-dashboard':
            await interaction.response.send_message(self.vat_guard_dashboard(int_branch), ephemeral=True)
        else:
            await interaction.response.send_message(self.vat_sup_dashboard(int_branch), ephemeral=True)

    def vat_guard_dashboard(self, branch: Branch) -> str:
        now = datetime.datetime.now()

        vats_by_guard = {}
        for discord_user in branch.guild.members:
            if branch.guild.get_role(branch.guild_role_ids['lifeguard']) in discord_user.roles:
                vats_by_guard[discord_user.id] = 0

        # Adding the number of VATs to each guards total
        vats = self.fred.ymca.database.select_vats_month(branch, now)
        for vat in vats:
            if vat.guard_discord_id in vats_by_guard:
                vats_by_guard[vat.guard_discord_id] += 1

        # Splitting the guards into who has and hasn't been VATed for the month
        vbg_complete = {}
        vbg_incomplete = {}
        for guard in vats_by_guard:
            if vats_by_guard.get(guard) > 0:
                vbg_complete[guard] = vats_by_guard.get(guard)
            else:
                vbg_incomplete[guard] = vats_by_guard.get(guard)

        vbg_complete = {k: v for k, v in sorted(vbg_complete.items(), key=lambda item: item[1], reverse=True)}
        vats_complete_formatted = [f'Guard: <@{guard}>: {vbg_complete.get(guard)}\n' for guard in vbg_complete]
        vats_incomplete_formatted = [f'Guard: <@{guard}>: {vbg_incomplete.get(guard)}\n' for guard in vbg_incomplete]
        return f"# Summary of VATs (Guards, {now.strftime('%B %Y')}):\n{''.join(vats_complete_formatted)}## --------------------\n{''.join(vats_incomplete_formatted)}"
    
    def vat_sup_dashboard(self, branch: Branch) -> str:
        now = datetime.datetime.now()
        database = self.fred.ymca.database

        vats_by_sup = {}
        for discord_user in branch.guild.members:
            if branch.guild.get_role(branch.guild_role_ids['supervisor']) in discord_user.roles:
                # number of vats, number of shifts, ratio of vats per shift
                vats_by_sup[discord_user.id] = [0, 0, 0.0]

        # Adding the number of VATs to each sup total
        vats = database.select_vats_month(branch, now)
        for vat in vats:
            if vat.sup_discord_id in vats_by_sup:
                vats_by_sup[vat.sup_discord_id][0] += 1

        vbs_incomplete = {}
        shift_dict_by_sup = branch.w2w_client.shifts_sorted_by_employee_id(datetime.date(now.year, now.month, 1), now.date(), [branch.w2w_client.supervisor])
        for w2w_employee_id, shift_list in shift_dict_by_sup.items():
            discord_user = database.select_discord_user(branch, branch.get_w2w_employee_by_id(w2w_employee_id))
            if discord_user and discord_user.id in vats_by_sup:
                num_of_shifts = len(shift_list)
                num_of_vats = vats_by_sup[discord_user.id][0]
                ratio = num_of_vats / num_of_shifts if num_of_shifts else 0.0
                if num_of_shifts > num_of_vats:
                    vats_by_sup.pop(discord_user.id)
                    vbs_incomplete[discord_user.id] = [num_of_vats, num_of_shifts, ratio]
                else:
                    vats_by_sup[discord_user.id][1] = num_of_shifts



        vbs_complete = {k: v for k, v in sorted(vats_by_sup.items(), key=lambda item: item[1][2], reverse=True)}
        vbs_incomplete = {k: v for k, v in sorted(vbs_incomplete.items(), key=lambda item: item[1][1])}
        vbs_complete_formatted = [f'<@{id}>\t{values[0]}\t{values[1]}\t{values[2]}\n' for id, values in vbs_complete.items()]
        vbs_incomplete_formatted = [f'<@{id}>\t{values[0]}\t{values[1]}\t{values[2]}\n' for id, values in vbs_incomplete.items()]
        return f"# Summary of VATs (Supervisors, {now.strftime('%B %Y')}):\n## Name, Number of VATs, Number of Shifts, Ratio\n{''.join(vbs_complete_formatted)}## --------------------\n{''.join(vbs_incomplete_formatted)}"



async def setup(fred: Fred):
    fred.tree.add_command(Formstack_Commands(name="form", description="Commands for fetching information from Formstack", fred=fred))
