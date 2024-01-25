from __future__ import annotations

from .pool import Pool
from typing import TYPE_CHECKING, List, Union

if TYPE_CHECKING:
    from whentowork.models import Position

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
