from unittest import TestCase
from whentowork import Employee
import fred
from settings import SETTINGS_DICT


class BranchTestCase(TestCase):
    def setUp(self):
        ymca = fred.YMCA('YMCA of Delaware')
        self.branch_western = ymca.branches['007']
        
    def test_branch_name(self):
        self.assertEqual('Western', self.branch_western.name)

    def test_get_w2w_employee_by_id(self):
        test_emp = self.branch_western.get_w2w_employee_by_id(564685546)
        self.assertIsInstance(test_emp, Employee)