from io import StringIO

from discord import Message

from database import execute_get, execute_write
from utilities import *


class MessageHandler:
	@property
	def current(self) -> int:
		return execute_get('SELECT current_count FROM game_state')[0][0]

	@current.setter
	def current(self, value: int) -> None:
		execute_write('UPDATE game_state SET current_count = %s', (value,))

	@property
	def next(self) -> int:
		return execute_get('SELECT current_count FROM game_state')[0][0] + 1

	@property
	def last_counted(self) -> Optional[int]:
		return execute_get('SELECT last_user_id FROM game_state')[0][0]

	@last_counted.setter
	def last_counted(self, value: Optional[int]) -> None:
		if value is not None:
			execute_write('UPDATE game_state SET last_user_id = %s', (value,))

	def get_response(self, message: Message) -> Response:
		user_input: str = message.content.lower().strip()
		author_id: int = message.author.id

		for key, value in REPLACEMENT_SYMBOLS.items():
			user_input = user_input.replace(key, str(value))

		if not all(character in SUPPORTED_CHARACTERS for character in user_input):
			return Response()

		if not execute_get('SELECT * FROM users WHERE user_id = %s', (author_id,)):
			execute_write(
				'INSERT INTO users (user_id, correct_count, incorrect_count, max_count) VALUES (%s, %s, %s, %s)',
				(author_id, 0, 0, 0)
			)

		try:
			result: int = round(eval(user_input))
		except (SyntaxError, ValueError, TypeError):
			return Response()
		except ZeroDivisionError:
			return Response('You can\'t divide by **0**!')

		if self.last_counted == author_id:
			self.lose(author_id)
			return Response(
				f'**Incorrect**, {message.author.mention}! You can\'t count twice in a row! The next number is **1**!',
				is_number=True, is_valid_number=False)

		if result == self.next:
			self.current += 1
			execute_write('UPDATE users SET correct_count = correct_count + 1 WHERE user_id = %s', (author_id,))
			self.last_counted = author_id
			return Response(None, True, True)
		else:
			self.lose(author_id)
			return Response(f'**Incorrect**, {message.author.mention}! The next number is **1**!', True, False)

	def lose(self, author_id: int) -> None:
		self.current = 0
		self.last_counted = 0
		execute_write('UPDATE users SET incorrect_count = incorrect_count + 1 WHERE user_id = %s', (author_id,))

	def get_leaderboard(self, order: str) -> str:
		users = execute_get(
			f'SELECT user_id, {order} FROM users WHERE is_blacklisted = FALSE ORDER BY {order} DESC LIMIT %s',
			(LEADERBOARD_COUNT,)
		)

		if not users:
			return 'Not enough data :('

		string_io: StringIO = StringIO()

		for index, (user_id, value) in enumerate(users, start=1):
			match index:
				case 1:
					string_io.write(f':trophy:')
				case 2:
					string_io.write(f':second_place:')
				case 3:
					string_io.write(f':third_place:')
				case _:
					string_io.write(f'{index}.')

			if order == 'accuracy':
				string_io.write(f' **<@{user_id}>**: **{value:,.1%}**\n')
			else:
				string_io.write(f' **<@{user_id}>**: **{value}**\n')

		return string_io.getvalue()

	def get_user_stats(self, user_id: int) -> str:
		response = execute_get(
			'SELECT correct_count, incorrect_count, max_count, accuracy FROM users WHERE user_id = %s',
			(user_id,)
		)

		if not response:
			return 'No data on the user'

		correct, incorrect, max_count, accuracy = response[0]

		return (f':white_check_mark: Correct: **{correct}**\n'
		        f':x: Incorrect: **{incorrect}**\n'
		        f':trophy: Max count: **{max_count}**\n'
		        f':dart: Accuracy: **{accuracy:,.1%}**')


message_handler: MessageHandler = MessageHandler()
