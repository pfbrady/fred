from __future__ import annotations

from ..w2w import YMCAW2WClient
from .pool_group import PoolGroup
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ymca import YMCA
    from ..types.w2w import YMCAW2WClientPayload

log = logging.getLogger(__name__)

class Branch(object):
    def __init__(self, ymca: YMCA, branch_id: str, branch: dict):
        self.ymca = ymca
        self.branch_id = branch_id
        self.name = branch['name']
        self.guild_id = branch['guild_id']
        self.aquatic_director = branch['aquatic_director']
        self.aquatic_specialists = branch['aquatic_specialists']
        self.pool_groups = [PoolGroup(self, pool_group_id, pool_group) for pool_group_id, pool_group in branch['pool_groups'].items()]
        self._update_w2w_client(branch['w2w_custom_hostname'], branch['w2w_token'], branch['w2w_position_ids'])

    def get_w2w_employee_by_id(self, w2w_employee_id: int):
        return self.w2w_client.get_employee_by_id(w2w_employee_id)

    def _update_w2w_client(self, w2w_custom_hostname: str, w2w_token: str, w2w_position_ids: YMCAW2WClientPayload):
        try:
            self.w2w_client = YMCAW2WClient(w2w_custom_hostname, w2w_token, w2w_position_ids)
        except Exception as e:
            log.error(msg=f'W2W Client not connected for branch {self.name}: {str(e)}')