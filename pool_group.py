import w2w
import datetime
name_options = {'main', 'complex'}

class PoolGroup(object):
    def __init__(self, name):
        if name not in name_options:
            raise ValueError(f"Pool: name must be one of {name_options}")
        self.name = name
        