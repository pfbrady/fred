from unittest import TestCase, skip
import datetime
from fred.ymca import YMCA, Pool
from settings import SETTINGS_DICT

class PoolTestCase(TestCase):
    def setUp(self):
        ymca = YMCA('YMCA of Delaware')
        self.pool_complex_lap = ymca.branches['007'].pool_groups[0].pools[0]
         
    def test_pool_name(self):
        self.assertEqual('Complex Lap Pool', self.pool_complex_lap.name)

    @skip('not set up properly')
    def test_update_extreme_times(self):
        self.pool_complex_lap.update_extreme_times()
        self.assertEqual(self.pool_complex_lap, (datetime.time(5, 45), datetime.time(18, 0)))
          