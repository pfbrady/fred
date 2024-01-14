from unittest import TestCase
from fred.ymca import YMCA
from settings import SETTINGS_DICT


class BranchTestCase(TestCase):
    def setUp(self):
        ymca = YMCA('YMCA of Delaware')
        self.branch_western = ymca.branches['007']
         
    def test_branch_name(self):
        self.assertEqual('Western', self.branch_western.name)