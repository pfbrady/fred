import feedparser
from html.parser import HTMLParser
import settings

class FormstackHTMLParser(HTMLParser):
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
        if self.key_flag == True:
            self.last_key = data[:-1]
            self.form_dict[data[:-1]] = None
            self.key_flag = False
        elif self.value_flag == True:
            self.form_dict[self.last_key] = data

def form_rss_to_dict(link: str):
    fp = feedparser.parse(link)
    parsed_entries = []
    for entry in fp.entries:
        form_parser = FormstackHTMLParser()
        form_parser.feed(entry.content[0].value)
        parsed_entries.append(form_parser.form_dict)
    return parsed_entries

print(form_rss_to_dict(settings.FORM_OPENING_CLOSING_RSS))