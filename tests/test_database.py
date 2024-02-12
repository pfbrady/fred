from unittest import TestCase
from fred import YMCA
import discord

class YMCADatabaseCase(TestCase):
    def setUp(self):
        ymca = YMCA('YMCA of Delaware')
        self.test_branch = ymca.branches['007']
        self.test_employee = self.test_branch.w2w_client.employees[0]
        self.test_pool = self.test_branch.pool_groups[0].pools[0]
        self.database = ymca.database

         
    def test_database_connection(self):
        self.assertEqual(True, bool(self.database.connection))
    
    def test_select_last_chem(self):
        last_chem = self.database.select_last_chem(self.test_branch, self.test_pool)
        print(last_chem)
        self.assertIsNotNone(last_chem)

    def test_select_discord_users(self):
        user: discord.Member = self.database.select_discord_user(self.test_branch, self.test_employee)
        print(user)
        self.assertIsNotNone(user)

