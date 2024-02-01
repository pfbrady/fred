from unittest import TestCase
from fred import database_helper

class DBHTestCase(TestCase):        
    def test_handle_quotes(self):
        self.assertEqual("Hell''o H''i", database_helper.handle_quotes("Hell'o", "H'i"))