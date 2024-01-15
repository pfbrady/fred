from __future__ import annotations

from .. import daxko
from datetime import time, date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pool_group import PoolGroup


class Pool(object):
    def __init__(self, pool_group: PoolGroup, pool_id: str, pool: dict):
        self.pool_group = pool_group
        self.pool_id = pool_id
        self.name = pool['name']
        self.aliases = pool['aliases']
        self.is_open = False
        self.opening_time = None
        self.closing_time = None

    def update_deps(self):
        self.update_extreme_times()
        self.update_is_open()

    def update_is_open(self):
        self.is_open = True if self.name in daxko.get_open_pools() else False

    def update_extreme_times(self):
        today_shifts = self.pool_group.branch.w2w_client.get_shifts_by_date(date.today(), date.today())

        if not today_shifts:
            self.opening_time, self.closing_time = (None, None)

        extreme_times = None
        for shift in today_shifts:
            if not extreme_times:
                extreme_times = (shift.start_datetime, shift.end_datetime)
            if shift.start_datetime < extreme_times[0]:
                extreme_times[0] = shift.start_datetime
            if shift.end_datetime > extreme_times[1]:
                extreme_times[1] = shift.end_datetime
        self.opening_time, self.closing_time = extreme_times
         