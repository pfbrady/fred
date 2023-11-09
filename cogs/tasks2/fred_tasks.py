import discord
from discord.ext import commands, tasks
import get_open_shifts as gos
import datetime
import pytz

from itertools import cycle

#status = cycle(['status 1', 'status 2', 'status 3'])

class Tasks(commands.Cog):


    def __init__(self, Fred):
        self.Fred = Fred
        self.send_unassigned_shifts.start()
        self.send_last_chem.start()

    #EVENTS
    '''
    @commands.Cog.listener()
    async def on_member_join(self, context, member):
        await context.send(f'Member {member.mention} has joined!')
    
    #TASKS
    @tasks.loop(seconds=10.0)
    async def change_stats(self):
        await self.dBot.change_presence(activity=discord.Game(next(status)))
    '''
    @tasks.loop(seconds=10.0)
    async def send_last_chem(self):
        print("run-chems")
        for guild in self.Fred.guilds:
            for channel in guild.text_channels:
                if channel.name == 'test3':
                    print("logic good for chems")
                    await channel.send(f"The last chem check completed was: {self.Fred.database.select_last_chem()}")

    @tasks.loop(seconds=10.0)
    async def send_unassigned_shifts(self):
        print("run")
        shifts_tuple = gos.open_shifts()
        shifts_as_int = [int(shift) for shift in shifts_tuple]
        lifeguard_unassigned_shifts, aquatic_lead_unassigned_shifts, swim_instr_unassigned_shifts = shifts_as_int
        current_time = datetime.datetime.now(pytz.timezone('US/Eastern'))
        print(current_time.hour)

        if current_time.hour == 14:
            for guild in self.Fred.guilds:
                for channel in guild.text_channels:
                    if channel.name == 'test' and lifeguard_unassigned_shifts != 0:
                        await channel.send(f"Hi, there are ({lifeguard_unassigned_shifts}) unassigned Lifeguard shifts tomorrow.")
                    elif channel.name == 'test' and aquatic_lead_unassigned_shifts != 0:
                        await channel.send(f"Hi, there are ({aquatic_lead_unassigned_shifts}) unassigned Supervisor shifts tomorrow.")
                    elif channel.name == 'test' and swim_instr_unassigned_shifts != 0:
                        await channel.send(f"Hi, there are ({swim_instr_unassigned_shifts}) unassigned Swim Instructor shifts tomorrow.")

    #COMMANDS

async def setup(Fred):
    await Fred.add_cog(Tasks(Fred))