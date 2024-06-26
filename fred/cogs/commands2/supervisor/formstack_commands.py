from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import discord

from fred.cogs.commands2.command_helper import platform_auto
from fred.dashboard import SupervisorReport, GuardReport, ReportType

if TYPE_CHECKING:
    from fred.fred import Fred
    from fred.chem import ChemCheck
    from typing import List


class FormstackCommands(discord.app_commands.Group):
    def __init__(self, name, description, fred: Fred):
        super().__init__(name=name, description=description)
        self.fred: Fred = fred

    async def chems_pool_auto(self, interaction: discord.Interaction, current: str
                              ) -> List[discord.app_commands.Choice[str]]:
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

    @discord.app_commands.command(description="Summary of chemical checks for the indicated pools.")
    @discord.app_commands.describe(
        pool="Specific pool location. Options are listed above.",
        platform="The platform you are on.")
    @discord.app_commands.autocomplete(pool=chems_pool_auto, platform=platform_auto)
    async def chems(self, interaction: discord.Interaction, pool: str, platform: str):
        int_branch = self.fred.ymca.get_branch_by_guild_id(interaction.guild_id)
        selected_chems: List[ChemCheck] = []
        for pool_group in int_branch.pool_groups:
            if pool in pool_group.aliases:
                selected_chems.extend(self.fred.ymca.database.select_last_chems(int_branch, pool_group.pools))
                continue
            for pool_obj in pool_group.pools:
                if pool in pool_obj.aliases or pool == 'all':
                    selected_chems.append(self.fred.ymca.database.select_last_chem(int_branch, pool_obj))

        chems_formatted = []
        for chem in selected_chems:
            sel_pool = int_branch.get_pool_by_pool_id(chem.pool_id)
            pool_name = sel_pool.name if sel_pool else 'Pool Name Error'
            chems_formatted.append(
                f'Name: <@{chem.discord_id}>\n Chem Check ID: {chem.chem_uuid}\n Pool: {pool_name}\n'
                f'Chlorine: {chem.chlorine}\t\tpH: {chem.ph}\n Temperature: {chem.water_temp}\n'
                f'Number of Swimmers: {chem.num_of_swimmers}\n Time: {chem.time}\n\n')
        await interaction.response.send_message(f"# Summary of Chem Checks:\n{''.join(chems_formatted)}",
                                                ephemeral=True)

    async def vats_pool_auto(self, interaction: discord.Interaction, current: str
                             ) -> List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=default_pos, value=default_pos)
            for default_pos in [
                'last',
                'guard-dashboard',
                'sup-dashboard',
                'guard-plot',
                'sup-plot'] if current in default_pos
        ]

    @discord.app_commands.command(description="Summary of VAT information.")
    @discord.app_commands.describe(
        group="Type of VAT summary you would like to see.",
        platform="The platform you are on.")
    @discord.app_commands.autocomplete(group=vats_pool_auto, platform=platform_auto)
    async def vats(self, interaction: discord.Interaction, group: str, platform: str):
        int_branch = self.fred.ymca.get_branch_by_guild_id(interaction.guild_id)
        now = datetime.datetime.now()
        if group == 'last':
            vat = self.fred.ymca.database.select_last_vat(int_branch)
            pool = int_branch.get_pool_by_pool_id(vat.pool_id)
            pool_name = pool.name if pool else 'Pool Name Error'
            vat_formatted = (f'Guard Name: <@{vat.guard_discord_id}>\n Supervisor Name: <@{vat.sup_discord_id}>\n'
                             f'VAT ID: {vat.vat_uuid}\n Pool: {pool_name}\n Number of Swimmers: {vat.num_of_swimmers}\n'
                             f'Number of Guards: {vat.num_of_guards}\n Stimuli: {vat.stimuli}\n Pass?: {vat.vat_pass}\n'
                             f'Response Time (s): {vat.response_time}\n Time: {vat.time}\n\n')
            await interaction.response.send_message(f"# Most Recent VAT:\n{vat_formatted}", ephemeral=True)
        elif 'plot' in group:
            if group == 'guard-plot':
                report = GuardReport(ReportType.MTD, now)
            else:
                report = SupervisorReport(ReportType.MTD, now)
            report.run_report(int_branch, interaction.user, include_vats=True)
            await report.send_report_plot(interaction=interaction)
        else:
            if group == 'guard-dashboard':
                report = GuardReport(ReportType.MTD, now)
            else:
                report = SupervisorReport(ReportType.MTD, now)
            report.run_report(int_branch, interaction.user, include_vats=True)
            await report.send_report(interaction=interaction, mobile=(platform == 'mobile'))


async def setup(fred: Fred):
    fred.tree.add_command(
        FormstackCommands(name="form", description="Commands for fetching information from Formstack.", fred=fred))
