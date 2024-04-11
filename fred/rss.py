"""rss.py module"""

from __future__ import annotations

import datetime
from html.parser import HTMLParser
from typing import TYPE_CHECKING

import feedparser

if TYPE_CHECKING:
    from typing import List, Union, Dict


class FormstackHTMLParser(HTMLParser):
    """
    Parser for Formstack's RSS links.

    Inherits from HTMLParser
    """

    def __init__(self):
        HTMLParser.__init__(self)
        self.form_dict = {}
        self.key_flag = False
        self.value_flag = False
        self.last_key = None

    def handle_starttag(self, tag, attrs):
        if tag == 'strong':
            self.key_flag = True
        elif tag == 'p':
            self.value_flag = True

    def handle_endtag(self, tag):
        if tag == 'strong':
            self.key_flag = False
        elif tag == 'p':
            self.value_flag = False

    def handle_data(self, data):
        if self.key_flag:
            self.last_key = data[:-1]
            self.form_dict[data[:-1]] = None
            self.key_flag = False
        elif self.value_flag:
            self.form_dict[self.last_key] = data.strip()


def form_rss_to_dict(link: str) -> List[Dict[str, Union[str, int, datetime]]]:
    fp: feedparser.FeedParserDict = feedparser.parse(link)
    parsed_entries: List[Dict[str, Union[str, int, datetime]]] = []
    for entry in fp.entries:
        form_parser = FormstackHTMLParser()
        form_parser.feed(entry.content[0].value)
        parsed_entries.append(form_parser.form_dict)
        parsed_entries[-1]['Time'] = datetime.datetime.strptime(
            entry.published, '%a, %d %b %Y %X %z').replace(tzinfo=None)
        parsed_entries[-1]['Unique ID'] = int(
            entry.link.split('/view/')[1].split('/')[0])
    parsed_entries.reverse()
    return parsed_entries
