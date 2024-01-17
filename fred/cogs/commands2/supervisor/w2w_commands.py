import datetime
import typing
import discord
from discord.ext import commands, tasks
import w2w

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from fred import Fred, Branch
    from whentowork import Position, Shift

class W2W_Commands(discord.app_commands.Group):
    def __init__(self, name, description, fred):
        super().__init__(name=name, description=description)
        self.fred: Fred = fred
        self.guards_default_times = ['now', 'earlier-today', 'later-today', 'today', 'today-closers', 'tomorrow', 'tomorrow-openers', 'tomorrow-closers', 'week', 'week-openers', 'week-closers']
        self.guards_default_pos = ['all', 'complex', 'main']
        self.instructors_default_times = ['earlier-today', 'later-today', 'today', 'tomorrow', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
        self.instructors_default_pos = ['all', 'group', 'privates', 'swam']

    @discord.app_commands.command()
    async def testy(self, interaction:discord.Interaction):
        self.fred.ymca.database.update_tables_rss()
        await interaction.response.send_message(f'hrloo')

    async def guards_time_auto(self, interaction: discord.Interaction, current: str
    )-> typing.List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=default_time, value=default_time) 
            for default_time in self.guards_default_times if current.lower() in default_time.lower()
        ]
    
    async def guards_pos_auto(self, interaction: discord.Interaction, current: str
    )-> typing.List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=default_pos, value=default_pos) 
            for default_pos in self.guards_default_pos if current.lower() in default_pos.lower()
        ]
    
    @staticmethod
    def get_shifts_from_auto(int_branch: Branch, position_auto: str, time_auto: str):
        int_w2w_client = int_branch.w2w_client
        positions: List[Position] = []
        positions.append(int_w2w_client.get_position_by_id(int_w2w_client.specialist_id))
        positions.append(int_w2w_client.get_position_by_id(int_w2w_client.supervisor_id))
        for pool_group in int_branch.pool_groups:
            if position_auto == 'all':
                positions.append(int_w2w_client.get_position_by_id(pool_group.w2w_lifeguard_position_id))
            elif position_auto in pool_group.aliases:
                positions.append(int_w2w_client.get_position_by_id(pool_group.w2w_lifeguard_position_id))

        if time_auto == 'now':
            return int_w2w_client.get_shifts_now(positions)
        else:
            return []

    @discord.app_commands.command(description="guards")
    @discord.app_commands.describe(time="The time group which you intend to send a message to. Options are listed above.")
    @discord.app_commands.autocomplete(time=guards_time_auto, position=guards_pos_auto)
    async def guards(self, interaction:discord.Interaction, time: str, position: str, message: str):
        int_branch = self.fred.ymca.get_branch_by_guild_id(interaction.guild_id)
        shifts = self.get_shifts_from_auto(int_branch, position, time)
        w2w_employees = int_branch.w2w_client.unique_employees(shifts)        
        discord_users = self.fred.ymca.database.select_discord_users([emp.w2w_employee_id for emp in w2w_employees])
        await interaction.response.send_message(f"Notification: {' '.join([f'<@{id}>' for id in discord_users])}: {message}")
  
    async def instructors_time_auto(self, interaction: discord.Interaction, current: str
    )-> typing.List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=default_time, value=default_time) 
            for default_time in self.instructors_default_times if current.lower() in default_time.lower()
        ]
    
    async def instructors_pos_auto(self, interaction: discord.Interaction, current: str
    )-> typing.List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=default_pos, value=default_pos) 
            for default_pos in self.instructors_default_pos if current.lower() in default_pos.lower()
        ]

    @discord.app_commands.describe(time="The time group which you intend to send a message to. Options are listed above.")
    @discord.app_commands.autocomplete(time=instructors_time_auto, position=instructors_pos_auto) 
    @discord.app_commands.command(description="instructors")
    async def instructors(self, interaction:discord.Interaction, time: str, position: str, message: str):
        w2w_pos = w2w.w2wpos_from_default_pos(position, w2w.W2WPosition.INSTRUCTORS)
        w2w_users = w2w.w2w_from_default_time(time, w2w_pos)
        employees = self.fred.database.select_discord_users(w2w_users)
        employees_formatted = [f'<@{id}>' for id in employees]
        await interaction.response.send_message(f"__Notification__: {' '.join(employees_formatted)}: {message}.", ephemeral=True)

async def setup(fred):
    fred.tree.add_command(W2W_Commands(name="w2w", description="test", fred=fred))