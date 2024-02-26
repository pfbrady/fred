from __future__ import annotations

from .w2w import YMCAW2WClient
from .pool_group import PoolGroup
import logging
from whentowork import Employee
from typing import TYPE_CHECKING, List, Dict, Optional, Union

if TYPE_CHECKING:
    from .ymca import YMCA
    from .pool import Pool
    from .types.w2w import YMCAW2WClientPayload
    from discord import Guild, Member

log = logging.getLogger(__name__)

class Branch(object):
    def __init__(self, ymca: YMCA, branch_id: str, branch: Dict):
        self.ymca: YMCA = ymca
        self.branch_id: str = branch_id
        self.name: str = branch['name']
        self.aliases: List[str] = branch['aliases']
        self.aquatic_director: str = branch['aquatic_director']
        self.aquatic_specialists: str = branch['aquatic_specialists']

        self.guild_id: int = branch['guild_id']
        self.guild: Union[Guild, None] = None
        self.guild_role_ids: Dict[str, Dict[str, int]] = branch['discord_role_ids']
        self.test_guild_id: int = branch['test_guild_id']
        self.test_guild = None
        self.test_guild_role_ids: Dict[str, Dict[str, int]] = branch['discord_test_role_ids']

        self.pool_groups: List[PoolGroup] = [PoolGroup(branch_id, pool_group_id, pool_group) for pool_group_id, pool_group in branch['pool_groups'].items()]
        self._update_w2w_client(branch['w2w_custom_hostname'], branch['w2w_token'], branch['w2w_position_ids'])
        
        self.rss_links: Dict[str, str] = branch['rss_links']
        self.last_chem_id: int = 0
        self.last_vat_id: int = 0
        self.last_opening_id: int = 0
        self.last_closing_id: int = 0
        self.last_in_service_id: int = 0

    def get_pool_by_pool_id(self, pool_id: str) -> Optional[Pool]:
        for pool_group in self.pool_groups:
            for pool in pool_group.pools:
                if pool_id == pool.pool_id:
                    return pool
        return None
    
    def get_discord_member_by_id(self, discord_user_id: int) -> Optional[Member]:
        user = self.guild.get_member(discord_user_id)
        return user if user else None

    def get_w2w_employee_by_id(self, w2w_employee_id: int) -> Optional[Employee]:
        employee = self.w2w_client.get_employee_by_id(w2w_employee_id)
        return employee if employee else None
        # employee = self.ymca.database.select_w2w_employee(w2w_employee_id)

    def _update_w2w_client(self, w2w_custom_hostname: str, w2w_token: str, w2w_position_ids: YMCAW2WClientPayload):
        try:
            self.w2w_client = YMCAW2WClient(w2w_custom_hostname, w2w_token, w2w_position_ids)
        except Exception as e:
            log.error(msg=f'W2W Client not connected for branch {self.name}: {str(e)}')

    def init_w2w_positions(self):
        for pool_group in self.pool_groups:
            pool_group.w2w_lifeguard_position = self.w2w_client.get_position_by_id(pool_group.w2w_lifeguard_position_id)
            pool_group.w2w_supervisor_position = self.w2w_client.get_position_by_id(pool_group.w2w_supervisor_position_id)

    def update_pool_groups(self):
        for pool_group in self.pool_groups:
            pool_group.update_pools(self.w2w_client.get_shifts_today([pool_group.w2w_lifeguard_position]))