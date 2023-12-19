import ymcabranch as yb

class YMCA(object):
    def __init__(self, name):
        self.name = name
        self.branches = [yb.YMCABranch.fromname('western')]