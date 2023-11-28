import discord
from discord.ext import commands, tasks
import get_open_shifts as gos
import datetime
import pytz
import w2w
import pool as pl
import cogs.commands2.supervisor.w2w_commands as w2w_comm
import daxko


from itertools import cycle

#status = cycle(['status 1', 'status 2', 'status 3'])

class Tasks(commands.Cog):


    def __init__(self, fred):
        self.fred = fred
        #self.send_unassigned_shifts.start()
        #self.send_last_chem.start()
        self.update_tables.start()

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
    # @tasks.loop(seconds=30.0)
    # async def send_last_chem(self):
    #     for guild in self.fred.guilds:
    #         for channel in guild.text_channels:
    #             if channel.name == 'test3':
    #                 await channel.send(f"The last chem check completed was: {self.Fred.database.select_last_chem(['Indoor Pool'])}")
    
    @tasks.loop(minutes=10)
    async def update_tables(self):
        updates = self.fred.database.update_tables_rss()
        open_pools = [pl.Pool(pool) for pool in daxko.get_open_pools()]
        for pool in open_pools:
            for guild in self.fred.guilds:
                for channel in guild.text_channels:
                    if channel.name == 'test3':
                        await channel.send(f"Updated Chems/VATs/Opening&Closing: {updates}")
                        last_chem = self.fred.database.select_last_chem([pool.name])
                        now = datetime.datetime.now()
                        if (last_chem[0][7] < str(now - datetime.timedelta(hours=2, minutes=30))
                            and now > pool.opening_time + datetime.timedelta(hours=2, minutes=30)
                            and now < pool.closing_time - datetime.timedelta(minutes=30)
                        ):
                            w2w_pos = w2w.w2wpos_from_default_pos(pool.group, w2w.W2WPosition.GUARDS)
                            w2w_users = w2w.w2w_from_default_time('now', w2w_pos)
                            employees = self.fred.database.select_discord_users(w2w_users)
                            employees_formatted = [f'<@{id}>' for id in employees]
                            await channel.send(f"Notification: {' '.join(employees_formatted)} Please submit a chemical check for the {pool.name}.")

    # @tasks.loop(seconds=10.0)
    # async def send_unassigned_shifts(self):
    #     print("run")
    #     shifts_tuple = gos.open_shifts()
    #     shifts_as_int = [int(shift) for shift in shifts_tuple]
    #     lifeguard_unassigned_shifts, aquatic_lead_unassigned_shifts, swim_instr_unassigned_shifts = shifts_as_int
    #     current_time = datetime.datetime.now(pytz.timezone('US/Eastern'))
    #     print(current_time.hour)

    #     if current_time.hour == 14:
    #         for guild in self.fred.guilds:
    #             for channel in guild.text_channels:
    #                 if channel.name == 'test' and lifeguard_unassigned_shifts != 0:
    #                     await channel.send(f"Hi, there are ({lifeguard_unassigned_shifts}) unassigned Lifeguard shifts tomorrow.")
    #                 elif channel.name == 'test' and aquatic_lead_unassigned_shifts != 0:
    #                     await channel.send(f"Hi, there are ({aquatic_lead_unassigned_shifts}) unassigned Supervisor shifts tomorrow.")
    #                 elif channel.name == 'test' and swim_instr_unassigned_shifts != 0:
    #                     await channel.send(f"Hi, there are ({swim_instr_unassigned_shifts}) unassigned Swim Instructor shifts tomorrow.")

    #COMMANDS
    @commands.command()
    async def ping(self, context):
        print("pong?")
        await context.send("Pong!")

    @commands.command()
    async def shifts(self, context, start_date=None, role=None):
        print("shifts?")
        shifts_info = w2w.get_assigned_shifts(start_date, role)
        await context.send(shifts_info)

async def setup(fred):
    await fred.add_cog(Tasks(fred))