import w2w
import pool as pl
import datetime

class PoolGroup(object):
    def __init__(self, name, pools):
        self.name = name
        self.pools = pools
    
    @classmethod
    def fromname(cls, name):
        if name not in {'main', 'complex'}:
            raise ValueError(f"Pool: name must be one of {{'main', 'complex'}}")
        if name == 'main':
            pool_names = ('Indoor Pool', '10-Lane Pool')
        else:
            pool_names = ('Complex Lap Pool', 'Complex Family Pool')
        pools = [pl.Pool.fromname(names) for names in pool_names]
        return cls(name, pools)