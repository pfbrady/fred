from unittest import TestCase
from fred import YMCA

class YMCADatabaseCase(TestCase):
    def setUp(self):
        ymca = YMCA('YMCA of Delaware')
        self.database = ymca.database

         
    def test_database_connection(self):
        self.assertEqual(True, bool(self.database.connection))

