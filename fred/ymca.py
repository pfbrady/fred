from __future__ import annotations

from typing import Dict, List, TYPE_CHECKING
from discord import Guild
from .branch import Branch
from .database import YMCADatabase #, YMCADatabaseConnectionManager
from settings import SETTINGS_DICT

if TYPE_CHECKING:
    from fred import Fred

class YMCA(object):
    def __init__(self, name: str):
        self.name: str = name
        self.branches: Dict[str, Branch] = {branch_id: Branch(self, branch_id, branch) for branch_id, branch in SETTINGS_DICT['branches'].items() if branch_id == '007'}
        self.database: YMCADatabase = YMCADatabase(self)
        # with YMCADatabaseConnectionManager() as database:

    
    def get_branch_by_guild_id(self, guild_id: int):
        for branch in self.branches.values():
            if branch.guild_id == guild_id:
                return branch
    
    def setup(self, guilds: List[Guild]):
        for branch in self.branches.values():
            for guild in guilds:
                if branch.guild_id == guild.id:
                    branch.guild = guild
                elif branch.test_guild_id == guild.id:
                    branch.test_guild = guild
            branch.init_w2w_positions()
            branch.update_pools()
