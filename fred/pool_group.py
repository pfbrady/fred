from __future__ import annotations

from typing import TYPE_CHECKING, List, Union
import datetime
from .pool import Pool

if TYPE_CHECKING:
    from whentowork import Position, Shift

class PoolGroup(object):
    def __init__(self, branch_id: str, pool_group_id: str, pool_group: dict):
        self.pool_group_id: str = pool_group_id
        self.branch_id: str = branch_id
        self.name: str = pool_group['name']
        self.aliases: List[str] = pool_group['aliases']
        self.w2w_lifeguard_position_id: int = pool_group['w2w_lifeguard_position_id']
        self.w2w_lifeguard_position: Union[Position, int] = None
        self.w2w_supervisor_position_id: int = pool_group['w2w_supervisor_position_id']
        self.w2w_supervisor_position: Union[Position, int] = None
        self.pools: List[Pool] = [Pool(branch_id, pool_group_id, pool_id, pool) for pool_id, pool in pool_group['pools'].items()]

    def update_pools(self, shifts: List[Shift]):
        for pool in self.pools:
            pool.update_is_open()

        if not shifts:
            for pool in self.pools:
                pool.is_open = False
                pool.opening_time, pool.closing_time = None, None
        else:
            extreme_times: List[datetime.datetime] = []
            for shift in shifts:
                if not extreme_times:
                    extreme_times = [shift.start_datetime, shift.end_datetime]
                if shift.start_datetime < extreme_times[0]:
                    extreme_times[0] = shift.start_datetime
                if shift.end_datetime > extreme_times[1]:
                    extreme_times[1] = shift.end_datetime
            for pool in self.pools:
                pool.opening_time, pool.closing_time = extreme_times
