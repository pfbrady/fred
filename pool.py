import w2w
import datetime
name_options = {'Indoor Pool', '10-Lane Pool', 'Complex Lap Pool', 'Complex Family Pool'}

class Pool(object):
    def __init__(self, name):
        if name not in name_options:
            raise ValueError(f"Pool: name must be one of {name_options}")
        if name == 'Indoor Pool' or '10-Lane Pool':
            self.group = 'main'
        else:
            self.group = 'complex'
        self.name = name
        self.now_dt = datetime.datetime.now()
        self.opening_time, self.closing_time = w2w.get_open_close_times_today([w2w.W2WPosition.LIFEGUARD_COMPLEX.value])
        