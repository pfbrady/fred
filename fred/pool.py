from __future__ import annotations

import fred.daxko as daxko
from typing import TYPE_CHECKING, List
import datetime

if TYPE_CHECKING:
    from .pool_group import PoolGroup


class Pool(object):
    def __init__(self, branch_id: str, pool_group_id: str, pool_id: str, pool: dict):
        self.pool_id: str = pool_id
        self.branch_id: str = branch_id
        self.pool_group_id: str = pool_group_id
        self.name: str = pool['name']
        self.aliases: List[str] = pool['aliases']
        self.is_open: bool = False
        self.opening_time: datetime.datetime = None
        self.closing_time: datetime.datetime = None
        self.checklists: List[str] = pool['checklists']
        self.chlorine: int = None
        self.ph: float = None

    def update_deps(self):
        self.update_is_open()

    def update_is_open(self):
        self.is_open = True if self.name in daxko.get_open_pools() else False
         