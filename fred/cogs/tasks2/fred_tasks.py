from __future__ import annotations

import discord
from discord.ext import commands, tasks
import datetime
import pytz
from fred.dashboard import SupervisorReport, GuardReport, ReportType
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from fred import Fred
    from whentowork import Position


from itertools import cycle

#status = cycle(['status 1', 'status 2', 'status 3'])


class Tasks(commands.Cog):
    def __init__(self, fred):
        self.fred: Fred = fred
        self.tasks = [
            self.update_tables,
            self.send_vats_to_sups,
            self.check_pool_extreme_times
        ]
        for task in self.tasks:
            task.start()

    def cog_unload(self):
        for task in self.tasks:
            task.cancel()

    @tasks.loop(minutes=30)
    async def update_tables(self):
        for branch in self.fred.ymca.branches.values():
            self.fred.ymca.database.update_rss(branch)
            for pool_group in branch.pool_groups:
                for pool in pool_group.pools:
                    if pool.is_open:
                        for channel in branch.guild.text_channels:
                            if channel.name == 'test3':
                                last_chem = self.fred.ymca.database.select_last_chem(branch, pool)
                                now = datetime.datetime.now()
                                positions: List[Position] = [branch.w2w_client.specialist, branch.w2w_client.supervisor, pool_group.w2w_lifeguard_position]
                                shifts = branch.w2w_client.get_shifts_now(positions)
                                w2w_employees = branch.w2w_client.unique_employees(shifts)        
                                discord_users = self.fred.ymca.database.select_discord_users(branch, w2w_employees)
                                if (last_chem
                                    and now > last_chem.time + datetime.timedelta(hours=2, minutes=30)
                                    and now > pool.opening_time + datetime.timedelta(hours=2, minutes=30)
                                    and now < pool.closing_time - datetime.timedelta(minutes=30)
                                ):
                                    await channel.send(f"Notification: {' '.join([user.mention for user in discord_users])} Please submit a chemical check for the {pool.name}.")
                                last_opening = None
                                for checklist in pool.checklists:
                                    lo_candidate = self.fred.ymca.database.select_last_opening(branch, checklist)
                                    if lo_candidate:
                                        if not last_opening:
                                            last_opening = lo_candidate
                                        elif lo_candidate.time < last_opening.time:
                                            last_opening = lo_candidate
                                if (last_opening
                                    and now > last_opening.time + datetime.timedelta(hours=16)
                                    and now > pool.opening_time + datetime.timedelta(hours=1, minutes=30)
                                    and now < pool.closing_time - datetime.timedelta(minutes=30)
                                ):
                                    await channel.send(f"Notification: {' '.join([user.mention for user in discord_users])} Please submit an opening checklist for the {pool.name}.")

    @update_tables.before_loop
    async def before_update_tables(self):
        await self.fred.wait_until_ready()

    @tasks.loop(time=datetime.time(hour=14, minute=9, tzinfo=pytz.timezone('US/Eastern')))
    async def send_vats_to_sups(self):
        now = datetime.datetime.now()
        if now.day == 14 or 28:
            for branch in self.fred.ymca.branches.values():         
                for channel in branch.guild.text_channels:
                    if channel.name == 'test3':
                        report = SupervisorReport(ReportType.MTD, now)
                        report.run_report(branch, run_by=self.fred.user, include_vats=True)
                        await report.send_report(channel=channel, mobile=False)
    
    @send_vats_to_sups.before_loop
    async def before_send_vats_to_sups(self):
        await self.fred.wait_until_ready()

    @tasks.loop(time=datetime.time(hour=0, minute=15, tzinfo=pytz.timezone('US/Eastern')))
    async def check_pool_extreme_times(self):
        for branch in self.fred.ymca.branches.values():
            branch.update_pool_groups()
            for guild in self.fred.guilds:
                    for channel in guild.text_channels:
                        if channel.name == 'test3':
                            await channel.send(f"Updating opening/closing times for each pool at {branch.name} Branch.")

    @check_pool_extreme_times.before_loop
    async def check_pool_extreme_times(self):
        await self.fred.wait_until_ready()

async def setup(fred: Fred):
    await fred.add_cog(Tasks(fred))