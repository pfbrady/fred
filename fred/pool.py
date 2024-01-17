from __future__ import annotations

import fred.daxko as daxko
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pool_group import PoolGroup


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
        self.update_is_open()

    def update_is_open(self):
        self.is_open = True if self.name in daxko.get_open_pools() else False
         