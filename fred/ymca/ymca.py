from typing import Dict
from .branch import Branch
from .database import YMCADatabase
from settings import SETTINGS_DICT

class YMCA(object):
    def __init__(self, name: str):
        self.name: str = name
        self.branches: Dict[str, Branch] = {branch_id: Branch(self, branch_id, branch) for branch_id, branch in SETTINGS_DICT['branches'].items() if branch_id == '007'}
        self.database: YMCADatabase = YMCADatabase(self)
    
