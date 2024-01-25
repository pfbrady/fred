from unittest import TestCase, skip
import fred
from typing import List

class RSSTestCase(TestCase):
    def setUp(self):
        ymca = fred.YMCA('YMCA of Delaware')
        self.chems_rss_link = ymca.branches['007'].rss_links['chems']
        self.oc_rss_link = ymca.branches['007'].rss_links['oc']
        self.vats_rss_link = ymca.branches['007'].rss_links['vats']
         
    def test_form_rss_to_dict_return_type(self):
        self.assertIsInstance(fred.rss.form_rss_to_dict(self.chems_rss_link), List)
        self.assertIsInstance(fred.rss.form_rss_to_dict(self.oc_rss_link), List)

    def test_form_rss_to_dict(self):
        print(fred.rss.form_rss_to_dict(self.vats_rss_link))
        self.assertTrue(fred.rss.form_rss_to_dict(self.chems_rss_link))