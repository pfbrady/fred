from __future__ import annotations

from datetime import date
from ..w2w import YMCAW2WClient
from .pool_group import PoolGroup
import logging
from whentowork import Shift
from typing import TYPE_CHECKING, List, Dict, Tuple, Union

if TYPE_CHECKING:
    from .ymca import YMCA
    from ..types.w2w import YMCAW2WClientPayload

log = logging.getLogger(__name__)

class Branch(object):
    def __init__(self, ymca: YMCA, branch_id: str, branch: dict):
        self.ymca: YMCA = ymca
        self.branch_id: str = branch_id
        self.name: str = branch['name']
        self.guild_id: int = branch['guild_id']
        self.aquatic_director: str = branch['aquatic_director']
        self.aquatic_specialists: str = branch['aquatic_specialists']
        self.pool_groups: List[PoolGroup] = [PoolGroup(self, pool_group_id, pool_group) for pool_group_id, pool_group in branch['pool_groups'].items()]
        self._update_w2w_client(branch['w2w_custom_hostname'], branch['w2w_token'], branch['w2w_position_ids'])
        self.rss_links: Dict[str, str] = branch['rss_links']

    def get_w2w_employee_by_id(self, w2w_employee_id: int):
        return self.w2w_client.get_employee_by_id(w2w_employee_id)

    def _update_w2w_client(self, w2w_custom_hostname: str, w2w_token: str, w2w_position_ids: YMCAW2WClientPayload):
        try:
            self.w2w_client = YMCAW2WClient(w2w_custom_hostname, w2w_token, w2w_position_ids)
        except Exception as e:
            log.error(msg=f'W2W Client not connected for branch {self.name}: {str(e)}')

    def update_pool_extreme_times(self):
        today_shifts: List[Shift] = self.w2w_client.get_shifts_by_date(date.today(), date.today())

        if not today_shifts:
            for pool_group in self.pool_groups:
                for pool in pool_group.pools:
                    pool.opening_time, pool.closing_time = (None, None)

        extreme_times: Union[Tuple, None] = None
        for shift in today_shifts:
            if not extreme_times:
                extreme_times = (shift.start_datetime, shift.end_datetime)
            if shift.start_datetime < extreme_times[0]:
                extreme_times[0] = shift.start_datetime
            if shift.end_datetime > extreme_times[1]:
                extreme_times[1] = shift.end_datetime
        for pool_group in self.pool_groups:
            for pool in pool_group.pools:
                pool.opening_time, pool.closing_time = extreme_times