from __future__ import annotations

import datetime
import typing
import discord
import settings
from discord.ext import commands, tasks
import fred.w2w as w2w

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fred.fred import Fred

class Formstack_Commands(discord.app_commands.Group):
    def __init__(self, name, description, fred: Fred):
        super().__init__(name=name, description=description)
        self.fred: Fred = fred

    async def chems_pool_auto(self, interaction: discord.Interaction, current: str
    )-> typing.List[discord.app_commands.Choice[str]]:
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
        selected_chems = []
        for pool_group in int_branch.pool_groups:
            if pool in pool_group.aliases:
                selected_chems.append(self.fred.ymca.database.select_last_chems(pool_group.pools, int_branch))
            else:
                for pool_obj in pool_group.pools:
                    if pool in pool_obj.aliases:
                        selected_chems.append(self.fred.ymca.database.select_last_chems([pool_obj], int_branch))
                
        chems_formatted = [f'Name: <@{chem[0]}>\n Chem Check ID: {chem[1]}\n Pool: {chem[2]}\n Chlorine: {chem[3]}\t\tpH: {chem[4]}\n Temperature: {chem[5]}\n Number of Swimmers: {chem[6]}\n Time: {chem[7]}\n\n' for chem in selected_chems]
        await interaction.response.send_message(f"# Summary of Chem Checks:\n{''.join(chems_formatted)}", ephemeral=True)

    @discord.app_commands.command(description="vats")
    async def vats(self, interaction:discord.Interaction):
        int_branch = self.fred.ymca.get_branch_by_guild_id(interaction.guild_id)
        vat = self.fred.ymca.database.select_last_vat(int_branch)
        vat_formatted = f'Guard Name: <@{vat[0]}>\n Supervisor Name: <@{vat[1]}>\n VAT ID: {vat[2]}\n Pool: {vat[3]}\n Number of Swimmers: {vat[4]}\n Number of Guards: {vat[5]}\n Stimuli: {vat[6]}\n Pass?: {vat[7]}\n Response Time (s): {vat[8]}\n Time: {vat[9]}\n\n'
        await interaction.response.send_message(f"# Most Recent VAT:\n{vat_formatted}", ephemeral=True)

    #@discord.app_commands.check(is_supervisor)
    @discord.app_commands.command(description="Dashboard for the VATs submitted month-to-date in Formstack")
    async def vats_dashboard(self, interaction:discord.Interaction):
        now = datetime.datetime.now()
        int_branch = self.fred.ymca.get_branch_by_guild_id(interaction.guild_id)

        vats_by_guard = {}
        for discord_user in int_branch.guild.members:
            if interaction.guild.get_role(int_branch.guild_role_ids['lifeguard']) in discord_user.roles:
                vats_by_guard[discord_user.id] = 0

        # Adding the number of VATs to each guards total
        vats = self.fred.ymca.database.select_vats_month(now, int_branch)
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


async def setup(fred: Fred):
    fred.tree.add_command(Formstack_Commands(name="form", description="Commands for fetching information from Formstack", fred=fred))
