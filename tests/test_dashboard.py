from unittest import TestCase
from fred import YMCA
import fred.cogs.dashboard as dash
import datetime

class DashboardCase(TestCase):
    def setUp(self):
        ymca = YMCA('YMCA of Delaware')
        self.test_branch = ymca.branches['007']

         
    def test_vat_supervisor_dashboard(self):
        test_dashboard = dash.VATSupervisorDashboard(self.test_branch, datetime.datetime.now())
        print(test_dashboard.report_type)
        self.assertIsNotNone(test_dashboard)