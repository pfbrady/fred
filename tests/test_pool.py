from unittest import TestCase, skip
import datetime
from fred.ymca.pool import Pool
from settings import SETTINGS_DICT

class PoolTestCase(TestCase):
    def setUp(self):
        pool_group_id, pool_group = next(iter(SETTINGS_DICT['branches']['007']['pool_groups'].items()))
        eight_lane_pool_id, eight_lane_pool = next(iter(pool_group['pools'].items()))
        self.eight_lane_pool = Pool(None, eight_lane_pool_id, eight_lane_pool)
         
    @skip('not set up properly')
    def test_update_extreme_times(self):
        self.eight_lane_pool.update_extreme_times()
        self.assertEqual(self.eight_lane_pool.opening_time, (datetime.time(5, 45), datetime.time(18, 0)))
          