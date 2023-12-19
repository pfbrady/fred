import w2w
import daxko
import datetime

class Pool(object):
    def __init__(self, name, created_dt, is_open, positions, opening_time, closing_time):
        self.name = name
        self.created_dt: datetime.datetime = created_dt
        self.is_open: bool = is_open
        self.positions = positions
        self.opening_time = opening_time
        self.closing_time = closing_time

    @classmethod
    def fromname(cls, name):
        if name not in {'Indoor Pool', '10-Lane Pool', 'Complex Lap Pool', 'Complex Family Pool'}:
            raise ValueError(f"Pool: name must be one of {{'Indoor Pool', '10-Lane Pool', 'Complex Lap Pool', 'Complex Family Pool'}}")
        positions = [w2w.W2WPosition.LIFEGUARD_MAIN_BUILDING.value] if name in {'Indoor Pool', '10-Lane Pool'} else [w2w.W2WPosition.LIFEGUARD_COMPLEX.value]
        opening_time, closing_time = w2w.get_open_close_times_today(positions)
        is_open = True if name in daxko.get_open_pools() else False
        return cls(name, datetime.datetime.now(), is_open, positions, opening_time, closing_time)
    
    def update_extreme_times(self):
        self.opening_time, self.closing_time = w2w.get_open_close_times_today(self.positions)

    def update_is_open(self):
        self.is_open = True if self.name in daxko.get_open_pools() else False