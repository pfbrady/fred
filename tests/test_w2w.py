from unittest import TestCase, skip
from datetime import date, datetime
import fred
from whentowork import Position
from settings import SETTINGS_DICT

class W2WTestCase(TestCase):
    def setUp(self):
        ymca = fred.YMCA('YMCA of Delaware')
        self.ymca_w2w_client_western = ymca.branches['007'].w2w_client
        self.sample_start_date = date(2024, 1, 14)
        self.sample_end_date = date(2024, 1, 15)
         
    def test_ymca_w2w_client_company_id(self):
        self.assertEqual(35181500, self.ymca_w2w_client_western.company_id)

    def test_filter_shifts(self):
        today_shifts = self.ymca_w2w_client_western.get_shifts_by_date(self.sample_start_date, self.sample_end_date)
        start_dt = datetime(2024, 1, 14, 6, 30)
        end_dt = datetime(2024, 1, 14, 16, 30)
        positions = [self.ymca_w2w_client_western.get_position_by_id(self.ymca_w2w_client_western.supervisor_id)]
        filtered_today_shifts = self.ymca_w2w_client_western.filter_shifts(today_shifts, start_dt, end_dt, positions)
        self.assertEqual(len(filtered_today_shifts), 1)
          