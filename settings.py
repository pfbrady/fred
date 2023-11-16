import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
WESTERN_GUILD_ID = os.getenv('WESTERN_GUILD_ID')
W2W_TOKEN = os.getenv('W2W_TOKEN')

BASE_DIR = (os.path.dirname(__file__))