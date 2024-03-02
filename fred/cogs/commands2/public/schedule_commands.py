from __future__ import annotations

import datetime
import discord
from fred import SupervisorReport, GuardReport, ReportType
from whentowork import Position

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fred import Fred, ChemCheck, Shift, Branch
    from typing import List

class Schedule_Commands(discord.app_commands.Group):
    def __init__(self, name, description, fred: Fred):
        super().__init__(name=name, description=description)
        self.fred: Fred = fred

    async def w2w_pos_auto(self, interaction: discord.Interaction, current: str
    )-> List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=default_pos, value=default_pos) 
            for default_pos in ['all', 'guard', 'swim-instructor'] if current in default_pos
        ]
    
    @staticmethod
    def get_shifts_from_auto(int_branch: Branch, position_auto: str) -> List[Shift]:
        int_w2w_client = int_branch.w2w_client
        positions: List[Position] = []
        if position_auto == 'guard' or position_auto == 'all':
            for pos in int_w2w_client.lifeguard_positions:
                positions.append(pos)
        if position_auto == 'swim-instructor' or position_auto == 'all':
            for pos in int_w2w_client.swim_instructor_positions:
                positions.append(pos)
        for pos in int_w2w_client.leadership_positions:
            positions.append(pos)
        
        return int_w2w_client.get_shifts_now(positions)

    @discord.app_commands.command(description="Fetches an up-to-date schedule from WhenToWork")
    @discord.app_commands.describe(position="Type of VAT summary you would like to see. For dashboards, please select '-mobile' if you are on mobile to correctly resolve mentions.")
    @discord.app_commands.autocomplete(position=w2w_pos_auto)
    async def w2w(self, interaction:discord.Interaction, position: str):
        int_branch = self.fred.ymca.get_branch_by_guild_id(interaction.guild_id)
        shifts = self.get_shifts_from_auto(int_branch, position)
        if discord_users:
            await interaction.response.send_message(f"Notification: {' '.join([user.mention for user in discord_users])}: {message}")
        else:
            await interaction.response.send_message(f"No swim instructors working at the indicated time. Please adjust your parameters.", ephemeral=True)

async def setup(fred: Fred):
    fred.tree.add_command(Schedule_Commands(name="schedule", description="Commands for fetching schedule-realated information (W2W, Lap Lane, Pool Events, etc.)", fred=fred))
