import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
WESTERN_GUILD_ID = int(os.getenv('WESTERN_GUILD_ID'))
MEGIN_ROLE_ID = int(os.getenv('MEGIN_ROLE_ID'))
SUPERVISOR_ROLE_ID = int(os.getenv('SUPERVISOR_ROLE_ID'))
LIFEGUARD_ROLE_ID = int(os.getenv('LIFEGUARD_ROLE_ID'))

W2W_TOKEN = os.getenv('W2W_TOKEN')

BASE_DIR = (os.path.dirname(__file__))