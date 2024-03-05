from unittest import TestCase
from fred import YMCA, SupervisorReport, ReportType, Fred
from settings import SETTINGS_DICT
import datetime
import discord

class DashboardCase(TestCase):
    def setUp(self):
        ymca = YMCA('YMCA of Delaware')
        self.test_branch = ymca.branches['007']

         
    def test_vat_supervisor_dashboard(self):
        test_dashboard = SupervisorReport(ReportType.MTD, datetime.datetime.now())
        test_dashboard.run_report(self.test_branch)
        print(test_dashboard.supervisors)
        self.assertIsNotNone(test_dashboard)