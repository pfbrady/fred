"""pool_group.py module"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

from fred.pool import Pool

if TYPE_CHECKING:
    from typing import List, Union
    from whentowork import Position, Shift


class PoolGroup:
    """
    A collection of pools, grouped based on WhenToWork positions for the
    lifeguards. For example, if a lifeguard's W2W position includes two pools,
    then the PoolGroup will contain those two pools.
    """

    def __init__(self, branch_id: str, pool_group_id: str, pool_group: dict):
        self.pool_group_id: str = pool_group_id
        self.branch_id: str = branch_id
        self.name: str = pool_group['name']
        self.aliases: List[str] = pool_group['aliases']
        self.w2w_lifeguard_position_id: int = pool_group['w2w_lifeguard_position_id']
        self.w2w_lifeguard_position: Union[Position, int] = None
        self.w2w_supervisor_position_id: int = pool_group['w2w_supervisor_position_id']
        self.w2w_supervisor_position: Union[Position, int] = None
        self.pools: List[Pool] = [
            Pool(branch_id, pool_group_id, pool_id, pool)
            for pool_id, pool in pool_group['pools'].items()
        ]

    def update_pools(self, shifts: List[Shift]) -> None:
        """Updates the opening and closing times for each pool based on the
        provided shifts.

        This function determines the operational hours of each pool, setting
        their opening and closing times according to the earliest starting shift
        and the latest ending shift. If no shifts are provided, all pools will
        be marked as closed. Additionally, this method calls the
        `update_is_open` method on each pool, which is assumed to dynamically
        control each pool's current open/closed state based on Daxko.

        Args:
            shifts (List[Shift]): A list of Shift objects, each containing a
            start_datetime and end_datetime.
        """
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
