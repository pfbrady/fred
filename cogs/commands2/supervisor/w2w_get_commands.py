import datetime
import typing
import discord
from discord.ext import commands, tasks
import w2w
import fred as fr

class W2W_Get_Commands(discord.app_commands.Group):
    def __init__(self, name, description, fred):
        super().__init__(name=name, description=description)
        self.fred: fr.Fred = fred
        self.guards_default_times = ['now', 'today', 'today-closers', 'tomorrow', 'tomorrow-openers', 'tomorrow-closers']
        self.instructors_default_times = ['today', 'tomorrow', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']

    @discord.app_commands.command()
    async def test(self, interaction:discord.Interaction):
        await interaction.response.send_message(f'hrloo')

    async def guards_autocompletion(self, interaction: discord.Interaction, current: str
    )-> typing.List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=default_time, value=default_time) 
            for default_time in self.guards_default_times if current.lower() in default_time.lower()
        ]

    @discord.app_commands.command(description="guards")
    @discord.app_commands.describe(time="The time group which you intend to send a message to. Options are listed above.")
    @discord.app_commands.autocomplete(time=guards_autocompletion)
    async def guards(self, interaction:discord.Interaction, time: str ,message: str):
        now_staff = w2w.get_employees_now(w2w.W2WPosition.GUARDS.value)
        employees = self.fred.database.select_discord_users(now_staff)
        employees_formatted = [f'<@{id}>' for id in employees]
        print(time)
        await interaction.response.send_message(f"ATTENTION {' '.join(employees_formatted)}: {message}.")
    
    def dt_from_default_time(default_time: str, positions: [w2w.W2WPosition] = None):
        now = datetime.datetime.now()
        if default_time == 'now':
            return w2w.get_employees_now(positions)
        elif default_time == 'today':
            return w2w.get_employees(now, datetime.datetime(now.year, now.month, now.day, 23, 59), positions)
        elif default_time == 'today-closers':
            return w2w.get_employees(
                datetime.datetime(now.year, now.month, now.day, 19, 59), 
                datetime.datetime(now.year, now.month, now.day, 23, 59), 
                positions
            )
        elif default_time == 'tomorrow':
            return w2w.get_employees(
                datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1), 
                datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1, hours=23, minutes=59), 
                positions
            )
        elif default_time == 'tomorrow-openers':
            return w2w.get_employees(
                datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1), 
                datetime.datetime(now.year, now.month, now.day) + datetime.timedelta(days=1, hours=7, minutes=50), 
                positions
            )


    
    async def instructors_autocompletion(self, interaction: discord.Interaction, current: str
    )-> typing.List[discord.app_commands.Choice[str]]:
        return [
            discord.app_commands.Choice(name=default_time, value=default_time) 
            for default_time in self.instructors_default_times if current.lower() in default_time.lower()
        ]

    @discord.app_commands.describe(time="The time group which you intend to send a message to. Options are listed above.")
    @discord.app_commands.autocomplete(time=guards_autocompletion) 
    @discord.app_commands.command(description="instructors")
    async def instructors(self, interaction:discord.Interaction, message: str):
        now_staff = w2w.get_employees_now(w2w.W2WPosition.INSTRUCTORS.value)
        print(now_staff)
        employees = self.fred.database.select_discord_users(now_staff)
        employees_formatted = [f'<@{id}>' for id in employees]
        print(f"Unpacked list: {*employees_formatted,}")
        await interaction.response.send_message(f"ATTENTION {' '.join(employees_formatted)}: {message}.")

async def setup(Fred):
    Fred.tree.add_command(W2W_Get_Commands(name="w2w", description="test", fred=Fred))