from unittest import TestCase, skip
import fred
import datetime

class ChemsTestCase(TestCase):
    def setUp(self):
        self.sample_oc = fred.OpeningChecklist(1)
        ymca = fred.YMCA('YMCA of Delaware')
        self.branch_western = ymca.branches['007']
        self.database = ymca.database

    def test_from_database(self):
        oc = self.database.select_last_opening(self.branch_western, 'Indoor Pool')
        print(oc.oc_uuid)
        self.assertIsNotNone(oc)

          