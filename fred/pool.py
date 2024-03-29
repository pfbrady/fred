"""pool.py module"""

from __future__ import annotations

from typing import TYPE_CHECKING
import datetime
import fred.daxko as daxko

if TYPE_CHECKING:
    from typing import List, Optional


class Pool(object):
    def __init__(self, branch_id: str, pool_group_id: str, pool_id: str, pool: dict):
        self.pool_id: str = pool_id
        self.branch_id: str = branch_id
        self.pool_group_id: str = pool_group_id
        self.name: str = pool['name']
        self.aliases: List[str] = pool['aliases']
        self.is_open: bool = False
        self.opening_time: Optional[datetime.datetime] = None
        self.closing_time: Optional[datetime.datetime] = None
        self.chlorine: Optional[int] = None
        self.ph: Optional[float] = None
        self.checklists: List[str] = pool['checklists']

    def update_is_open(self):
        self.is_open = True if self.name in daxko.get_open_pools() else False
         