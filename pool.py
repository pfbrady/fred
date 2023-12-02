import w2w
import datetime

class Pool(object):
    def __init__(self, name, created_dt, opening_time, closing_time):
        self.name = name
        self.created_dt = created_dt
        self.opening_time = opening_time
        self.closing_time = closing_time

    @classmethod
    def fromname(cls, name):
        if name not in {'Indoor Pool', '10-Lane Pool', 'Complex Lap Pool', 'Complex Family Pool'}:
            raise ValueError(f"Pool: name must be one of {{'Indoor Pool', '10-Lane Pool', 'Complex Lap Pool', 'Complex Family Pool'}}")
        opening_time, closing_time = w2w.get_open_close_times_today([w2w.W2WPosition.LIFEGUARD_COMPLEX.value])
        return cls(name, datetime.datetime.now(), opening_time, closing_time)