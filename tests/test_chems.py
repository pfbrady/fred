from unittest import TestCase, skip
import fred
import datetime

class ChemsTestCase(TestCase):
    def setUp(self):
        self.sample_chem = fred.ChemCheck(123, 3.0, 7.4)
        ymca = fred.YMCA('YMCA of Delaware')
        self.branch_western = ymca.branches['007']
        self.pool_complex = self.branch_western.pool_groups[0].pools[0]
        self.pool_indoor = self.branch_western.pool_groups[1].pools[1]
        self.database = ymca.database
         
    def test_chem_check_uuid(self):
        self.assertEqual(123, self.sample_chem.chem_uuid)

    def test_from_rss_entry(self):
        rss_entry = {'Branch': 'Western',
                     'Western': 'Complex Lap Pool',
                     'Location of Water Sample, Western': 'Complex Lap Pool | \
                        The water sample was taken from the pool edge by the \
                            lifeguard chair on the family pool side',
                     'Your Name': 'TEST NAME',
                     'Date/Time': 'Jan 30, 2024 08:28 PM',
                     'Chlorine': '1.00',
                     'PH': '7.60',
                     'Water Temperature': 'No Thermometer',
                     'Total Number of Swimmers': '2',
                     'Time': datetime.datetime(2024, 1, 30, 20, 29, 26),
                     'Unique ID': 1}
        self.assertEqual(1, fred.ChemCheck.from_rss_entry(self.branch_western, rss_entry).chem_uuid)

    def test_from_database(self):
        chem = self.database.select_last_chem(self.branch_western, self.pool_complex)
        print(chem)
        chem2 = self.database.select_last_chem(self.branch_western, self.pool_indoor)
        print(chem2)
        self.assertIsNotNone(chem.chem_uuid)

          