from unittest import TestCase, mock
from fred.ymca.ymca import YMCA
from settings import SETTINGS_DICT


class YMCATestCase(TestCase):
    def setUp(self):
        self.ymca = YMCA('YMCA of Delaware')
         
    def test_branches(self):
        self.assertIn('007', self.ymca.branches)