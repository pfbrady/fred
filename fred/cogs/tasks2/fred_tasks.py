import discord
from discord.ext import commands, tasks
import datetime
import pytz
import fred.w2w as w2w
import fred.pool as pl
import fred.daxko as daxko
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fred import Fred


from itertools import cycle

#status = cycle(['status 1', 'status 2', 'status 3'])

class Tasks(commands.Cog):


    def __init__(self, fred):
        self.fred: Fred = fred
        # self.update_tables.start()
        # self.check_pool_extreme_times.start()

    #EVENTS
    @commands.Cog.listener()
    async def on_member_join(self, context, member):
        for guild in self.fred.guilds:
            for channel in guild.text_channels:
                if channel.name == 'test3':
                    await context.send(f'Member {member.mention} has joined!')

    @tasks.loop(minutes=30)
    async def update_tables(self):
        updates = self.fred.database.update_tables_rss()
        for branch in self.fred.ymca.branches:
            for pool_group in branch.pool_groups:
                for pool in pool_group.pools:
                    if pool.is_open:
                        guild = self.fred.get_guild(branch.guild_id)
                        if not guild:
                            raise Exception(f"No guild found for {branch.name}.")
                        for channel in guild.text_channels:
                            if channel.name == 'test3':
                                last_chem = self.fred.database.select_last_chem([pool.name], branch.branch_id)
                                now = datetime.datetime.now()
                                if (last_chem[0][7] < str(now - datetime.timedelta(hours=2, minutes=30))
                                    and now > pool.opening_time + datetime.timedelta(hours=2, minutes=30)
                                    and now < pool.closing_time - datetime.timedelta(minutes=30)
                                ):
                                    w2w_pos = w2w.w2wpos_from_default_pos(pool_group.name, w2w.W2WPosition.GUARDS)
                                    w2w_users = w2w.w2w_from_default_time('now', w2w_pos)
                                    employees = self.fred.database.select_discord_users(w2w_users)
                                    employees_formatted = [f'<@{id}>' for id in employees]
                                    await channel.send(f"Notification: {' '.join(employees_formatted)} Please submit a chemical check for the {pool.name}.")
                                
                                last_opening = self.fred.database.select_last_opening(pool.name, branch.branch_id)
                                if (last_opening[7] < str(now - datetime.timedelta(hours=16))
                                    and now > pool.opening_time + datetime.timedelta(hours=1, minutes=30)
                                    and now < pool.closing_time - datetime.timedelta(minutes=30)
                                ):
                                    w2w_pos = w2w.w2wpos_from_default_pos(pool_group.name, w2w.W2WPosition.GUARDS)
                                    w2w_users = w2w.w2w_from_default_time('now', w2w_pos)
                                    employees = self.fred.database.select_discord_users(w2w_users)
                                    employees_formatted = [f'<@{id}>' for id in employees]
                                    await channel.send(f"Notification: {' '.join(employees_formatted)} Please submit an opening checklist for the {pool.name}.")

    @tasks.loop(time=datetime.time(hour=0, minute=15, tzinfo=pytz.timezone('US/Eastern')))
    async def check_pool_extreme_times(self):
        for branch in self.fred.ymca.branches:
            for pool_group in branch.pool_groups:
                for pool in pool_group.pools:
                    pool.update_extreme_times()
                    pool.update_is_open()
                    for guild in self.fred.guilds:
                            for channel in guild.text_channels:
                                if channel.name == 'test3':
                                    await channel.send("updating info")

async def setup(fred):
    await fred.add_cog(Tasks(fred))