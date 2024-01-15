from __future__ import annotations

from .pool import Pool
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .branch import Branch

class PoolGroup(object):
    def __init__(self, branch: Branch, pool_group_id: str, pool_group: dict):
        self.branch = branch
        self.pool_group_id = pool_group_id
        self.name = pool_group['name']
        self.aliases = pool_group['aliases']
        self.w2w_lifeguard_position_id = pool_group['w2w_lifeguard_position_id']
        self.w2w_supervisor_position_id = pool_group['w2w_supervisor_position_id']
        self.pools = [Pool(self, pool_id, pool) for pool_id, pool in pool_group['pools'].items()]
