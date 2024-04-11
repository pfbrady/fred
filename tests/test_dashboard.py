import datetime
from unittest import TestCase
from unittest.mock import MagicMock

from fred import YMCA, SupervisorReport, ReportType


class DashboardCase(TestCase):
    def setUp(self):
        ymca = YMCA('YMCA of Delaware')
        self.test_branch = ymca.branches['007']

    def test_vat_supervisor_dashboard(self):
        test_dashboard = SupervisorReport(ReportType.MTD, datetime.datetime.now())
        test_user = MagicMock()
        test_user.display_name = "TEST"
        test_dashboard.run_report(self.test_branch, test_user)
        test_dashboard.send_report_plot()
        self.assertIsNotNone(test_dashboard)
