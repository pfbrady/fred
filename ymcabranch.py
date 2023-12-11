import w2w
import poolgroup as pg
import datetime

class YMCABranch(object):
    def __init__(self, name, branch_id, pool_groups, aquatic_director = None, aquatic_specialists = None):
        self.name = name
        self.branch_id = branch_id
        self.aquatic_director = aquatic_director
        self.aquatic_specialists = aquatic_specialists
        self.pool_groups = pool_groups

    @classmethod
    def fromname(cls, name):
        if name not in {'western'}:
            raise ValueError(f"Pool: name must be one of {{'western'}}")
        pool_groups = [pg.PoolGroup.fromname(names) for names in {'main', 'complex'}]
        return cls(name, '007', pool_groups)
