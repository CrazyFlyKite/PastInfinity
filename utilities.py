import json
import platform
from dataclasses import dataclass
from os import getenv
from typing import List, Dict, Optional, Final

from discord.app_commands import Choice
from dotenv import load_dotenv

# Load the local environment
load_dotenv()


# Dataclasses
@dataclass(frozen=True)
class Response:
	message: Optional[str] = None
	is_number: Optional[bool] = False
	is_valid_number: Optional[bool] = False


# Secrets
TOKEN: Final[Optional[str]] = getenv('TOKEN')
MYSQL_USER: Final[Optional[str]] = getenv('MYSQL_USER')
MYSQL_PASSWORD: Final[Optional[str]] = getenv('MYSQL_PASSWORD')

# Checking IP
IS_NAS: Final[bool] = platform.system() == 'Linux'
HOST_IP: Final[Optional[str]] = '172.17.0.1' if IS_NAS else getenv('SYNOLOGY_IP')

# Constants
with open('config/constants.json', 'r', encoding='utf-8') as file:
	config = json.load(file)

DATABASE: Final[str] = config.get('database')
LEADERBOARD_COUNT: Final[int] = config.get('leaderboard_count')
TRUSTED_ROLES: List[str] = config.get('trusted_roles')
SUPPORTED_CHARACTERS: Final[str] = config.get('supported_characters')
REPLACEMENT_SYMBOLS: Final[Dict[str, float]] = config.get('replacement_symbols')
LEADERBOARD_ORDER_CHOICES: Final[List[Choice]] = [Choice(name=choice['name'], value=choice['value']) for choice in
                                                  config.get('leaderboard_order_choices')]

# Emojis
CORRECT_EMOJI: Final[str] = config.get('emojis').get('correct')
INCORRECT_EMOJI: Final[str] = config.get('emojis').get('incorrect')
FIRE_EMOJI: Final[str] = config.get('emojis').get('fire')
REPEAT_EMOJI: Final[str] = config.get('emojis').get('repeat')

# Information
DEVELOPER_IP: Final[int] = config.get('developer_id')

with open('config/info_template.md', 'r', encoding='utf-8') as file:
	INFORMATION: Final[str] = file.read().format(leaderboard_count=LEADERBOARD_COUNT, developer_id=DEVELOPER_IP)
