"""settings.py module"""

import json

with open('config.json') as json_file:
    data = json.load(json_file)

SETTINGS_DICT = data
