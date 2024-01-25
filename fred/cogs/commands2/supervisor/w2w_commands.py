from __future__ import annotations

import datetime
import typing
import discord

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from fred import Fred, Branch
    from whentowork import Position, Shift

class W2W_Commands(discord.app_commands.Group):
    def __init__(self, name, description, fred):
        super().__init__(name=name, description=description)
        self.fred: Fred = fred
        self.guards_default_times = ['now', 'earlier-today', 'later-today', 'today', 'today-closers', 'tomorrow', 'tomorrow-openers', 'tomorrow-closers', 'week', 'week-openers', 'week-closers']
        self.instructors_default_times = ['now', 'earlier-today', 'later-today', 'today', 'tomorrow']
        self.instructors_default_pos = ['all', 'group', 'private', 'swam']

    async def guards_time_auto(self, interaction:discord.Interaction, current: str
    )-> typing.List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=default_time, value=default_time) 
            for default_time in self.guards_default_times if current.lower() in default_time.lower()
        ]
    
    async def guards_pos_auto(self, interaction:discord.Interaction, current: str
    ) -> List[discord.app_commands.Choice[str]]:
        guards_default_pos = ['all']
        int_branch = self.fred.ymca.get_branch_by_guild_id(interaction.guild_id)
        for pool_group in int_branch.pool_groups:
            guards_default_pos.append(pool_group.name.replace(' ', '-').lower())
        return [
            discord.app_commands.Choice(name=default_pos, value=default_pos) 
            for default_pos in guards_default_pos if current.lower() in default_pos.lower()
        ]
    
    @staticmethod
    def get_shifts_from_auto(int_branch: Branch, position_auto: str, time_auto: str) -> List[Shift]:
        int_w2w_client = int_branch.w2w_client
        positions: List[Position] = []
        positions.append(int_w2w_client.specialist)
        positions.append(int_w2w_client.supervisor)
        for pool_group in int_branch.pool_groups:
            if position_auto == 'all':
                positions.append(int_w2w_client.get_position_by_id(pool_group.w2w_lifeguard_position_id))
            elif position_auto in pool_group.aliases:
                positions.append(int_w2w_client.get_position_by_id(pool_group.w2w_lifeguard_position_id))

        if time_auto == 'now':
            return int_w2w_client.get_shifts_now(positions)
        elif time_auto == 'today':
            return int_w2w_client.get_shifts_today(positions)
        elif time_auto == 'later-today':
            return int_w2w_client.get_shifts_later(positions)
        elif time_auto == 'earlier-today':
            return int_w2w_client.get_shifts_earlier(positions)
        elif time_auto == 'today-closers':
            today = datetime.date.today()
            return int_w2w_client.get_shifts_extreme(today, today, positions, False)
        
        elif time_auto == 'tomorrow':
            return int_w2w_client.get_shifts_tomorrow(positions)
        elif time_auto == 'tomorrow-openers':
            tomorrow = datetime.date.today() + datetime.timedelta(1)
            return int_w2w_client.get_shifts_extreme(tomorrow, tomorrow, positions, True)
        elif time_auto == 'tomorrow-closers':
            tomorrow = datetime.date.today() + datetime.timedelta(1)
            return int_w2w_client.get_shifts_extreme(tomorrow, tomorrow, positions, False)
        
        elif time_auto == 'week':
            today = datetime.date.today()
            return int_w2w_client.get_shifts(today, today + datetime.timedelta(7), positions)
        elif time_auto == 'week-openers':
            today = datetime.date.today()
            return int_w2w_client.get_shifts_extreme(today, today + datetime.timedelta(7), positions, True)
        elif time_auto == 'week-closers':
            today = datetime.date.today()
            return int_w2w_client.get_shifts_extreme(today, today + datetime.timedelta(7), positions, False)
                
        else:
            return []

    @discord.app_commands.command(description="Sends a notification to a group of guards, filtered by time and pool")
    @discord.app_commands.describe(time="The time group which you intend to send a message to. Options are listed above.")
    @discord.app_commands.autocomplete(time=guards_time_auto, position=guards_pos_auto)
    async def guards(self, interaction:discord.Interaction, time: str, position: str, message: str):
        int_branch = self.fred.ymca.get_branch_by_guild_id(interaction.guild_id)
        shifts = self.get_shifts_from_auto(int_branch, position, time)
        w2w_employees = int_branch.w2w_client.unique_employees(shifts)        
        discord_users = self.fred.ymca.database.select_discord_users(w2w_employees, int_branch)
        if discord_users:
            await interaction.response.send_message(f"Notification: {' '.join([user.mention for user in discord_users])}: {message}")
        else:
            await interaction.response.send_message(f"No lifeguards working at the indicated time. Please adjust your parameters.", ephemeral=True)
  
    async def instructors_time_auto(self, interaction:discord.Interaction, current: str
    )-> typing.List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=default_time, value=default_time) 
            for default_time in self.instructors_default_times if current.lower() in default_time.lower()
        ]
    
    async def instructors_pos_auto(self, interaction:discord.Interaction, current: str
    )-> typing.List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=default_pos, value=default_pos) 
            for default_pos in self.instructors_default_pos if current.lower() in default_pos.lower()
        ]

    @staticmethod
    def get_instructor_shifts_from_auto(int_branch: Branch, position_auto: str, time_auto: str) -> List[Shift]:
        int_w2w_client = int_branch.w2w_client
        positions: List[Position] = []
        if position_auto == 'group' or position_auto == 'all':
            positions.append(int_w2w_client.swim_instructor)
        if position_auto == 'private' or position_auto == 'all':
            positions.append(int_w2w_client.private_swim_instructor)
        if position_auto == 'swam' or position_auto == 'all':
            positions.append(int_w2w_client.swam)

        if time_auto == 'now':
            return int_w2w_client.get_shifts_now(positions)
        elif time_auto == 'today':
            return int_w2w_client.get_shifts_today(positions)
        elif time_auto == 'later-today':
            return int_w2w_client.get_shifts_later(positions)
        elif time_auto == 'earlier-today':
            return int_w2w_client.get_shifts_earlier(positions)
        
        elif time_auto == 'tomorrow':
            return int_w2w_client.get_shifts_tomorrow(positions)
        

        else:
            return []

    @discord.app_commands.describe(time="The time group which you intend to send a message to. Options are listed above.")
    @discord.app_commands.autocomplete(time=instructors_time_auto, position=instructors_pos_auto) 
    @discord.app_commands.command(description="Sends a notification to a group of swim instructors, filtered by time and position")
    async def instructors(self, interaction:discord.Interaction, time: str, position: str, message: str):
        int_branch = self.fred.ymca.get_branch_by_guild_id(interaction.guild_id)
        shifts = self.get_instructor_shifts_from_auto(int_branch, position, time)
        w2w_employees = int_branch.w2w_client.unique_employees(shifts)        
        discord_users = self.fred.ymca.database.select_discord_users(w2w_employees, int_branch.guild)
        if discord_users:
            await interaction.response.send_message(f"Notification: {' '.join([user.mention for user in discord_users])}: {message}")
        else:
            await interaction.response.send_message(f"No swim instructors working at the indicated time. Please adjust your parameters.", ephemeral=True)

async def setup(fred: Fred):
    fred.tree.add_command(W2W_Commands(name="w2w", description="Commands for fetching information from WhenToWork and sending messages to those who are working.", fred=fred))