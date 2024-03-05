from unittest import TestCase, mock
from fred import YMCA
from settings import SETTINGS_DICT


class YMCATestCase(TestCase):
    def setUp(self):
        self.ymca = YMCA('YMCA of Delaware')
        self.ymca.setup()
         
    def test_branches(self):
        self.assertIn('007', self.ymca.branches)