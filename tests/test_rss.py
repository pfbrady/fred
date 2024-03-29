"""test_rss module"""

from unittest import TestCase
from typing import List
import fred

class RSSTestCase(TestCase):
    """Test cases for rss.py"""
    def setUp(self):
        ymca = fred.YMCA('YMCA of Delaware')
        self.chems_rss_link = ymca.branches['007'].rss_links['chems']
        self.oc_rss_link = ymca.branches['007'].rss_links['oc']
        self.vats_rss_link = ymca.branches['007'].rss_links['vats']
        self.is_rss_link = ymca.branches['007'].rss_links['in_service']
         
    def test_form_rss_to_dict_return_type(self):
        self.assertIsInstance(fred.rss.form_rss_to_dict(self.chems_rss_link), List)
        self.assertIsInstance(fred.rss.form_rss_to_dict(self.oc_rss_link), List)

    def test_form_rss_to_dict(self):
        print(fred.rss.form_rss_to_dict(self.oc_rss_link))
        self.assertTrue(fred.rss.form_rss_to_dict(self.chems_rss_link))

    def test_form_rss_in_service(self):
        print(fred.rss.form_rss_to_dict(self.is_rss_link))
        self.assertTrue(fred.rss.form_rss_to_dict(self.chems_rss_link))
