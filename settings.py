import os
from dotenv import load_dotenv
import json

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

GUILD_ID_007 = int(os.getenv('GUILD_ID_007'))
DIRECTOR_ROLE_ID_007 = int(os.getenv('DIRECTOR_ROLE_ID_007'))
SUPERVISOR_ROLE_ID_007 = int(os.getenv('SUPERVISOR_ROLE_ID_007'))
LIFEGUARD_ROLE_ID_007 = int(os.getenv('LIFEGUARD_ROLE_ID_007'))

OC_RSS_007 = (os.getenv('OC_RSS_007'))
CHEMS_RSS_007 = (os.getenv('CHEMS_RSS_007'))
VATS_RSS_007 = (os.getenv('VATS_RSS_007'))

W2W_TOKEN_007 = os.getenv('W2W_TOKEN_007')

BASE_DIR = (os.path.dirname(__file__))

with open('ymca.json') as json_file:
    data = json.load(json_file)
for branch_id, branch_info in data['branches'].items():
    # SETTINGS_DICT.update({branch: 
    #     {'GUILD_ID': int(os.getenv(f'GUILD_ID_{branch}')),
    #      'DIRECTOR_ROLE_ID': int(os.getenv('DIRECTOR_ROLE_ID_007')),
    #      'SUPERVISOR_ROLE_ID': int(os.getenv('SUPERVISOR_ROLE_ID_007')),
    #      'LIFEGUARD_ROLE_ID': int(os.getenv('LIFEGUARD_ROLE_ID_007')),
    #      'OC_RSS': (os.getenv('OC_RSS_007')),
    #      'CHEMS_RSS': (os.getenv('CHEMS_RSS_007')),
    #      'VATS_RSS': (os.getenv('VATS_RSS_007')),
    #      'W2W_TOKEN': os.getenv('W2W_TOKEN_007')
    #     }})
    try:
        data['branches'][branch_id].update({'w2w_token': os.getenv(f'W2W_TOKEN_{branch_id}')})
    except KeyError: 
        print("no w2w connection")

SETTINGS_DICT = data