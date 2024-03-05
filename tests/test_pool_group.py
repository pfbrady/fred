from unittest import TestCase
from fred import YMCA
from settings import SETTINGS_DICT


class BranchTestCase(TestCase):
    def setUp(self):
        ymca = YMCA('YMCA of Delaware')
        self.pool_group_complex = ymca.branches['007'].pool_groups[0]
         
    def test_pool_group_name(self):
        self.assertEqual('Complex', self.pool_group_complex.name)