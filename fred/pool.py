from __future__ import annotations

import fred.daxko as daxko
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pool_group import PoolGroup


class Pool(object):
    def __init__(self, branch_id: str, pool_group_id: str, pool_id: str, pool: dict):
        self.pool_id = pool_id
        self.branch_id = branch_id
        self.pool_group_id = pool_group_id
        self.name = pool['name']
        self.aliases = pool['aliases']
        self.is_open = False
        self.opening_time = None
        self.closing_time = None
        self.chlorine = None
        self.ph = None

    def update_deps(self):
        self.update_is_open()

    def update_is_open(self):
        self.is_open = True if self.name in daxko.get_open_pools() else False
         