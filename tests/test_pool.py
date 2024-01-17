from unittest import TestCase, skip
from fred import YMCA, Pool
from settings import SETTINGS_DICT

class PoolTestCase(TestCase):
    def setUp(self):
        ymca = YMCA('YMCA of Delaware')
        self.pool_complex_lap = ymca.branches['007'].pool_groups[0].pools[0]
         
    def test_pool_name(self):
        self.assertEqual('Complex Lap Pool', self.pool_complex_lap.name)

          