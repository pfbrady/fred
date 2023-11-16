import datetime
import typing
import discord
from discord.ext import commands, tasks
import w2w
import fred as fr

class W2W_Commands(discord.app_commands.Group):
    def __init__(self, name, description, fred):
        super().__init__(name=name, description=description)
        self.fred: fr.Fred = fred
        self.guards_default_times = ['now', 'earlier-today', 'later-today', 'today', 'today-closers', 'tomorrow', 'tomorrow-openers', 'tomorrow-closers', 'week', 'week-openers', 'week-closers']
        self.guards_default_pos = ['all', 'complex', 'main']
        self.instructors_default_times = ['earlier-today', 'later-today', 'today', 'tomorrow', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
        self.instructors_default_pos = ['all', 'group', 'privates', 'swam']

    @discord.app_commands.command()
    async def test(self, interaction:discord.Interaction):
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
    

    @discord.app_commands.command(description="guards")
    @discord.app_commands.describe(time="The time group which you intend to send a message to. Options are listed above.")
    @discord.app_commands.autocomplete(time=guards_time_auto, position=guards_pos_auto)
    async def guards(self, interaction:discord.Interaction, time: str, position: str, message: str):
        w2w_pos = self.w2wpos_from_default_pos(position, w2w.W2WPosition.GUARDS)
        w2w_users = self.w2w_from_default_time(time, w2w_pos)
        employees = self.fred.database.select_discord_users(w2w_users)
        employees_formatted = [f'<@{id}>' for id in employees]
        await interaction.response.send_message(f"Notification: {' '.join(employees_formatted)}: {message}.")

    def w2wpos_from_default_pos(self, default_pos:str, type:w2w.W2WPosition):
        if default_pos == 'all':
            return type.value
        elif type == w2w.W2WPosition.GUARDS:
            if default_pos == 'complex':
                return [type.value[0], type.value[2]]
            else:
                return [type.value[1], type.value[2]]
        else: # if type is instructors
            if default_pos == 'group':
                return [type.value[1]]
            else:
                return [type.value[0]] # SWAM


    
    def w2w_from_default_time(self, default_time: str, positions: [w2w.W2WPosition] = None):
        now = datetime.datetime.now()
        if default_time == 'now':
            return w2w.get_employees_now(positions)
        elif default_time == 'earlier-today':
            return w2w.get_employees(datetime.datetime(now.year, now.month, now.day), now, positions)
        elif default_time == 'later-today':
            return w2w.get_employees(now, datetime.datetime(now.year, now.month, now.day, 23, 59), positions)
        elif default_time == 'today':
            return w2w.get_employees(datetime.datetime(now.year, now.month, now.day), datetime.datetime(now.year, now.month, now.day, 23, 59), positions)
        elif default_time == 'tomorrow':
            return w2w.get_employees(
                datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1), 
                datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1, hours=23, minutes=59), 
                positions
            )
        elif default_time == 'week':
            return w2w.get_employees(
                datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1), 
                datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=6, hours=23, minutes=59), 
                positions
            )
        elif default_time == 'today-closers':
            return w2w.get_employees(
                datetime.datetime(now.year, now.month, now.day, 19, 59), 
                datetime.datetime(now.year, now.month, now.day, 23, 59), 
                positions,
                'closers'
            )
        elif default_time == 'tomorrow-openers':
            return w2w.get_employees(
                datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1), 
                datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1, hours=23, minutes=59), 
                positions,
                'openers'
            )
        elif default_time == 'tomorrow-closers':
            return w2w.get_employees(
                datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1, hours=19, minutes=59), 
                datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1, hours=23, minutes=59), 
                positions,
                'closers'
            )
        elif default_time == 'week-openers':
            return w2w.get_employees(
                datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1, hours=19, minutes=59), 
                datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=6, hours=23, minutes=59), 
                positions,
                'openers'
            )
        elif default_time == 'week-openers':
            return w2w.get_employees(
                datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1, hours=19, minutes=59), 
                datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=6, hours=23, minutes=59), 
                positions,
                'closers'
            )
        else:
            weekdays = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6}
            today = datetime.datetime(now.year, now.month, now.day).weekday()
            delta = weekdays[default_time] - today
            if delta <= 0:
                delta += 7
            return w2w.get_employees(
                datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=delta), 
                datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=delta, hours=23, minutes=59), 
                positions
            )


    
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
        w2w_pos = self.w2wpos_from_default_pos(position, w2w.W2WPosition.INSTRUCTORS)
        w2w_users = self.w2w_from_default_time(time, w2w_pos)
        employees = self.fred.database.select_discord_users(w2w_users)
        employees_formatted = [f'<@{id}>' for id in employees]
        await interaction.response.send_message(f"__Notification__: {' '.join(employees_formatted)}: {message}.", ephemeral=True)

async def setup(Fred):
    Fred.tree.add_command(W2W_Commands(name="w2w", description="test", fred=Fred))