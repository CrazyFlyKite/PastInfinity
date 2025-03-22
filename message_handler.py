from io import StringIO

from discord import Message

from data_manager import data_manager
from utilities import *


class MessageHandler:
	def __init__(self) -> None:
		self._current_number = data_manager.load().get('current')
		self._last_counted = data_manager.load().get('last_counted')
		self._leaderboard = data_manager.load().get('leaderboard')
		self._blacklist: List[int] = data_manager.load().get('blacklist')
		self._super_blacklist: List[int] = data_manager.load().get('super_blacklist')

	@property
	def current(self) -> int:
		return self._current_number

	@current.setter
	def current(self, value: Any) -> None:
		self._current_number = value

	@property
	def next(self) -> int:
		return self._current_number + 1

	@property
	def leaderboard(self) -> Dict[str, UserStats]:
		return self._leaderboard

	@leaderboard.setter
	def leaderboard(self, value: Any) -> None:
		self._leaderboard = value

	@property
	def last_counted(self) -> Optional[int]:
		return self._last_counted

	@last_counted.setter
	def last_counted(self, value: Any) -> None:
		self._last_counted = value

	@property
	def blacklist(self) -> List[int]:
		return self._blacklist

	@blacklist.setter
	def blacklist(self, value: Any) -> None:
		self._blacklist = value

	@property
	def super_blacklist(self) -> List[int]:
		return self._super_blacklist

	def get_response(self, message: Message) -> Response:
		user_input: str = message.content.lower().strip()
		author_id: str = str(message.author.id)

		for key, value in REPLACEMENT_SYMBOLS.items():
			user_input = user_input.replace(key, str(value))

		if not all(character in SUPPORTED_CHARACTERS for character in user_input):
			return Response()

		if author_id not in self.leaderboard:
			self.leaderboard[author_id] = {'user': message.author.name, 'correct_count': 0, 'incorrect_count': 0,
			                               'max_count': 0}

		try:
			result: int = round(eval(user_input))
		except (SyntaxError, ValueError):
			return Response()
		except TypeError:
			return Response('You can\'t use **complex** numbers with me!')
		except ZeroDivisionError:
			return Response('You can\'t divide by **0**!')

		if str(self.last_counted) == author_id:
			self.lose(author_id)
			return Response(
				f'**Incorrect**, {message.author.mention}! You can\'t count twice in a row! The next number is **1**!',
				is_number=True, is_valid_number=False)

		if result == self.next:
			self.current += 1
			self.leaderboard[author_id]['correct_count'] += 1
			self.last_counted = int(author_id)
			self.leaderboard[author_id]['max_count'] = max(self.current, self.leaderboard[author_id]['max_count'])
			return Response(None, True, True)
		else:
			self.lose(author_id)
			return Response(f'**Incorrect**, {message.author.mention}! The next number is **1**!', True, False)

	def lose(self, message_author_id: str) -> None:
		self.current = 0
		self.last_counted = None
		self.leaderboard[message_author_id]['incorrect_count'] += 1

	def get_leaderboard(self) -> str:
		if not self.leaderboard:
			return 'Not enough data'

		string_io: StringIO = StringIO()
		sorted_users: List[UserStats] = sorted(self.leaderboard.values(), key=lambda x: x['correct_count'],
		                                       reverse=True)

		for index, user_stats in enumerate(sorted_users[:LEADERBOARD_COUNT], start=1):
			string_io.write(f"{index}. **{user_stats['user']}**: **{user_stats['correct_count']}**\n")

		return string_io.getvalue()

	def clear_leaderboard(self) -> None:
		self.current = 0
		self.last_counted = None
		self.leaderboard = {}

	def check_for_accuracy(self, author_id: int, user_stats: Optional[UserStats]) -> None:
		if user_stats is None:
			return

		if user_stats['correct_count'] + user_stats['incorrect_count'] > 10 and self.get_accuracy(user_stats) < 0.4:
			self.blacklist.append(author_id)

	@staticmethod
	def get_accuracy(user_stats: UserStats) -> float:
		correct_count, incorrect_count = user_stats['correct_count'], user_stats['incorrect_count']

		if correct_count + incorrect_count == 0:
			return 0.0
		else:
			return correct_count / (correct_count + incorrect_count)

	def get_user_stats(self, user_id: int) -> str:
		user_id = str(user_id)

		if user_id not in self.leaderboard:
			return 'No data on the user'

		user_stats: UserStats = self.leaderboard[user_id]
		correct_count: int = user_stats['correct_count']
		incorrect_count: int = user_stats['incorrect_count']
		accuracy: float = self.get_accuracy(user_stats)

		return f"Correct: **{correct_count}**\nIncorrect: **{incorrect_count}**\nMax count: **{user_stats['max_count']}**\nAccuracy: **{accuracy:,.1%}**"
