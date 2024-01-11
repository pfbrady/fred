import ymcabranch as yb
import settings

class YMCA(object):
    def __init__(self, name):
        self.name = name
        self.branches = [yb.YMCABranch.fromid(branch_id) for branch_id in {"007"}]
        # BELOW TO IMPLEMENT AFTER WESTERN IS ALL DONE
        # self.branches = [yb.YMCABranch.fromid(branch_id) for branch_id in settings.SETTINGS_DICT['branches']]