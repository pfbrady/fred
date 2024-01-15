from .branch import Branch
from settings import SETTINGS_DICT

class YMCA(object):
    def __init__(self, name: str):
        self.name = name
        self.branches = {branch_id: Branch(self, branch_id, branch) for branch_id, branch in SETTINGS_DICT['branches'].items() if branch_id == '007'}
