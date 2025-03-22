from dataclasses import dataclass
from os import getenv, PathLike
from typing import List, Dict, Optional, Any, Final, TypedDict, TypeAlias

from discord import Embed, Colour
from dotenv import load_dotenv

# Load the local environment
load_dotenv()

# Custom types
PathLikeString: TypeAlias = str | PathLike
JSONDictionary: TypeAlias = Dict[str, Any]


# Dataclasses and typed dictionaries
@dataclass(frozen=True)
class Response:
	message: Optional[str] = None
	is_number: Optional[bool] = False
	is_valid_number: Optional[bool] = False


class UserStats(TypedDict):
	user: str
	correct_count: int
	incorrect_count: int
	max_count: int


# Secrets
TOKEN: Final[str] = getenv('TOKEN')
EMAIL: Final[str] = getenv('EMAIL')
PASSWORD: Final[str] = getenv('PASSWORD')

# Constants
COMMAND_PREFIX: Final[str] = '/'
LEADERBOARD_COUNT: Final[int] = 10
TRUSTED_ROLES: List[str] = ['Dictator', 'Co-Owner', 'Admin', 'Mod']
GODLY_ROLES: List[str] = ['Dictator', 'Co-Owner']
SUPPORTED_CHARACTERS: Final[str] = '1234567890.+-*/%() '
REPLACEMENT_SYMBOLS: Final[Dict[str, float]] = {
	'π': 3.14159,
	'ϕ': 1.61803
}

# Emojis
CORRECT_EMOJI: Final[str] = '\U00002705'
INCORRECT_EMOJI: Final[str] = '\U0000274C'
FIRE_EMOJI: Final[str] = '\U0001F525'
HEART_EMOJI: Final[str] = '\U00002764'

# Information
AUTHOR: Final[int] = 873920068571000833
INFORMATION_MESSAGE: Final[str] = f'''
I'm keeping track of a sequence of numbers!

## How to Use
- Write a number in sequence to **continue the count**.
- If you write the wrong number, the counter will reset.
- You can use **Python** mathematical symbols: `+`, `-`, `*`, `/`, `**` (power), `()`
- You can't count immediately after yourself. You need to wait for someone else to continue before you can count again.
- There's some math constants that you can use: **π ≈ 3.14159**, **ϕ ≈ 1.61803**
- If you have accuracy less than **40%** (and at least **10** count attempts), you'll be **blacklisted**.

## Commands
`/next` - Shows the next number in the sequence
`/info` - Shows information about the bot and its functions
`/leaderboard` - Displays the TOP {LEADERBOARD_COUNT} users by the number of correct numbers
`/user_stats` - Shows the user's statistics
`/clear_leaderboard` - Clears the leaderboard history
`/switch_channel` - Changes the bot's channel to another
`/bake` - Saves all data about the bot
`/blacklist_add` - Adds user to the blacklist
`/blacklist_remove` - Removes user from the blacklist

## Note
The result is always **rounded** to the nearest whole number.
You need certain **roles** to use some commands.

## Author
[My Discord](<https://discord.com/users/{AUTHOR}>)
'''


# Functions
def embed(description: str, colour: Colour = Colour.blue(), title: Optional[str] = None,
          thumbnail: Optional[str] = None) -> Embed:
	embed_object: Embed = Embed(description=description, colour=colour)

	if title:
		embed_object.title = title

	if thumbnail:
		embed_object.set_thumbnail(url=thumbnail)

	return embed_object


def success_embed(description: str) -> Embed:
	return embed(description, Colour.green())


def error_embed(description: str) -> Embed:
	return embed(description, Colour.red())


def critical_embed(description: str) -> Embed:
	return embed(description, Colour.green())
