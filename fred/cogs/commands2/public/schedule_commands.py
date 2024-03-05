from __future__ import annotations

import datetime
import discord
from fred.cogs.commands2.command_helper import mobile_auto
from whentowork import Position

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fred import Fred, ChemCheck, Shift, Branch
    from typing import List, Dict

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
    def get_shifts_from_auto(
            int_branch: Branch,
            int_dt: datetime.datetime,
            position_auto: str) -> Dict[Position, List[Shift]]:
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
        
        return int_w2w_client.shifts_sorted_by_position(
            int_dt - datetime.timedelta(minutes=15),
            int_dt + datetime.timedelta(minutes=15),
            positions)

    @discord.app_commands.command(description="Fetches an up-to-date schedule from WhenToWork")
    @discord.app_commands.describe(
        position="Type of positions you would like to see. Leadership (Specialists and Supervisors) added automatically"
        ".")
    @discord.app_commands.describe(mobile="Select 'True' if you are on mobile to correctly resolve mentions and display"
        " a shorter message.")
    @discord.app_commands.autocomplete(position=w2w_pos_auto, mobile=mobile_auto)
    async def w2w(self, interaction:discord.Interaction, position: str, mobile: str):
        int_branch = self.fred.ymca.get_branch_by_guild_id(interaction.guild_id)
        now = datetime.datetime.now()
        w2w_shifts_by_pos = self.get_shifts_from_auto(int_branch, now, position)
        if w2w_shifts_by_pos and eval(mobile):
            content = self.format_employees(int_branch, w2w_shifts_by_pos, position, eval(mobile))
            await interaction.response.send_message(content, ephemeral=True)
        elif w2w_shifts_by_pos and not eval(mobile):
            content = self.format_employees(int_branch, w2w_shifts_by_pos, position, eval(mobile))
            title = f"Current Schedule on WhenToWork (Positions: {position.capitalize().replace('-', ' ')})"
            embed = discord.Embed(title=title, description=content)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(
                f"No employees for that position are currently working. Please adjust your parameters.",
                ephemeral=True)
            
    def format_employees(
            self,
            int_branch: Branch,
            w2w_shifts_by_pos: Dict[Position, List[Shift]],
            position_auto: str,
            mobile: bool) -> str:
        if mobile:
            content = f"## Current Schedule on WhenToWork (Positions: {position_auto.capitalize().replace('-', ' ')})\n"
            for pos, shifts in w2w_shifts_by_pos.items():
                content += f'**{pos.position_name}**\n'
                for shift in shifts:
                    w2w_guard_name = f'{shift.employee.first_name} {shift.employee.last_name}' if shift.employee else None
                    w2w_shift_time = (f"{shift.start_datetime.strftime('%I:%M%p')}-"
                        f"{shift.end_datetime.strftime('%I:%M%p')}")
                    content += f'{w2w_guard_name}, {w2w_shift_time}\n'
            return content[:2000]
        else:
            content = ''
            for pos, shifts in w2w_shifts_by_pos.items():
                content += f'**{pos.position_name}**\n'
                for shift in shifts:
                    discord_user = self.fred.ymca.database.select_discord_user(int_branch, shift.employee) if shift.employee else None
                    mention = discord_user.mention if discord_user else discord_user
                    w2w_shift_time = (f"{shift.start_datetime.strftime('%I:%M%p')}-"
                        f"{shift.end_datetime.strftime('%I:%M%p')}")
                    content += f'{mention}, {w2w_shift_time}\n'
            return content[:4096]




async def setup(fred: Fred):
    fred.tree.add_command(Schedule_Commands(name="schedule", description="Commands for fetching schedule-realated information (W2W, Lap Lane, Pool Events, etc.).", fred=fred))
