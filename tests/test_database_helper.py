from unittest import TestCase
from fred import database_helper, YMCA

class DBHTestCase(TestCase):
    def setUp(self):
        ymca = YMCA('YMCA of Delaware')
        self.western = ymca.branches['007']       
    def test_handle_quotes(self):
        self.assertEqual("Hell''o H''i", database_helper.handle_quotes("Hell'o", "H'i"))

    def test_match_pool_id_from_keys(self):
        self.assertEqual("007-01-01", database_helper.match_pool_id_from_dict(self.western, {"Western": "Complex Lap Pool"}))