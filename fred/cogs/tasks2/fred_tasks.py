"""fred_tasks module"""

from __future__ import annotations

from typing import TYPE_CHECKING
import datetime
import pytz
from discord.ext import commands, tasks
from fred.dashboard import SupervisorReport, ReportType

if TYPE_CHECKING:
    from typing import List
    from fred import Fred, Branch, PoolGroup, Pool
    from whentowork import Position
    from discord import TextChannel


# from itertools import cycle
#status = cycle(['status 1', 'status 2', 'status 3'])


class FredTasks(commands.Cog):
    """
    Discord Cog for regularly-scheduled tasks for FRED.

    Inherits from discord.ext.commands.Cog
    """
    def __init__(self, fred):
        self.fred: Fred = fred
        self.tasks = [
            self.update_tables,
            self.send_vats_to_sups,
            self.check_pool_extreme_times
        ]
        for task in self.tasks:
            task.start()

    async def cog_unload(self):
        for task in self.tasks:
            task.cancel()

    async def check_form_adherance(
            self,
            branch: Branch,
            pool_group: PoolGroup,
            pool: Pool,
            channel: TextChannel) -> None:
        """
        Checks that a chemical check has been completed in the last 2.5 hours
        and that an opening checklist was submitted. If one or more of those
        requirements are not fulfilled, it sends a message to the lifeguards
        currently scheduled for that pool and the leadership who are present in
        the building to submit the required form(s).

        Args:
            branch (Branch): The YMCA of DE Branch to check.
            pool_group (PoolGroup): The branch's group of pools to check.
            pool (Pool): The pool group's specific pool to check.
            channel (TextChannel): The channel to send a message in. Typically
            'fred-lg-notifs'.
        """
        last_chem = self.fred.ymca.database.select_last_chem(
            branch,
            pool
        )
        now = datetime.datetime.now()
        positions: List[Position] = [
            branch.w2w_client.specialist,
            branch.w2w_client.supervisor,
            pool_group.w2w_lifeguard_position
        ]
        shifts = branch.w2w_client.get_shifts_now(positions)
        w2w_employees = branch.w2w_client.unique_employees(shifts)
        discord_users = self.fred.ymca.database.select_discord_users(
            branch,
            w2w_employees
        )
        if (last_chem
            and now > last_chem.time + datetime.timedelta(hours=2, minutes=30)
            and now > pool.opening_time + datetime.timedelta(hours=2, minutes=30)
            and now < pool.closing_time - datetime.timedelta(minutes=30)
        ):
            await channel.send(
                f"Notification: {' '.join([user.mention for user in discord_users])}"
                f" Please submit a chemical check for the {pool.name}."
                )
        last_opening = None
        for checklist in pool.checklists:
            lo_candidate = self.fred.ymca.database.select_last_opening(
                branch,
                checklist
            )
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
            await channel.send(
                f"Notification: {' '.join([user.mention for user in discord_users])}"
                f" Please submit an opening checklist for the {pool.name}."
            )

    @tasks.loop(minutes=30)
    async def update_tables(self):
        """
        discord.py task that loops through all of the branches every 30
        minutes, and for each pool that is currently open, 
        """
        for branch in self.fred.ymca.branches.values():
            self.fred.ymca.database.update_rss(branch)
            for pool_group in branch.pool_groups:
                for pool in pool_group.pools:
                    if pool.is_open and branch.guild:
                        for channel in branch.guild.text_channels:
                            if channel.name == 'fred-lg-notif':
                                await self.check_form_adherance(
                                    branch,
                                    pool_group,
                                    pool,
                                    channel
                                )

    @update_tables.before_loop
    async def before_update_tables(self):
        """
        Waits for FRED to be logged in before running update_tables for the
        first time.
        """
        await self.fred.wait_until_ready()

    @tasks.loop(time=datetime.time(
        hour=14,
        minute=9,
        tzinfo=pytz.timezone('US/Eastern'))
    )
    async def send_vats_to_sups(self):
        """
        discord.py task that 
        """
        now = datetime.datetime.now()
        if now.day in (14, 28):
            for branch in self.fred.ymca.branches.values():
                if branch.guild:
                    for channel in branch.guild.text_channels:
                        if channel.name == 'sup-general':
                            report = SupervisorReport(ReportType.MTD, now)
                            report.run_report(
                                branch,
                                run_by=self.fred.user,
                                include_vats=True
                            )
                            await report.send_report(
                                channel=channel,
                                mobile=False
                            )

    @send_vats_to_sups.before_loop
    async def before_send_vats_to_sups(self):
        """
        Waits for FRED to be logged in before running send_vats_to_sups for
        the first time.
        """
        await self.fred.wait_until_ready()

    @tasks.loop(time=datetime.time(
        hour=0,
        minute=15,
        tzinfo=pytz.timezone('US/Eastern'))
    )
    async def check_pool_extreme_times(self):
        """
        discord.py task that loops through each branch every day at 12:15 AM
        and updates each pool's open and close times, as well as if the pool
        if open.
        """
        for branch in self.fred.ymca.branches.values():
            branch.update_pool_groups()
            for guild in self.fred.guilds:
                for channel in guild.text_channels:
                    if channel.name == 'test3':
                        await channel.send(
                            "Updating opening/closing times for each pool at "
                            f"{branch.name} Branch."
                            )

    @check_pool_extreme_times.before_loop
    async def before_check_pool_extreme_times(self):
        """
        Waits for FRED to be logged in before running check_pool_extreme_times
        for the first time.
        """
        await self.fred.wait_until_ready()

async def setup(fred: Fred):
    """
    Expected setup() function that adds FredTasks as a cog of FRED, thus
    registering its specified tasks.

    Args:
        fred (Fred): An instance of FRED
    """
    await fred.add_cog(FredTasks(fred))
