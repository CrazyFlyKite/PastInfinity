from io import StringIO

from discord import Message

from database import execute_get, execute_write
from utilities import *


class MessageHandler:
	async def get_current(self) -> int:
		return (await execute_get('SELECT current_count FROM game_state'))[0][0]

	async def set_current(self, value: int) -> None:
		await execute_write('UPDATE game_state SET current_count = %s', (value,))

	async def get_next(self) -> int:
		return (await self.get_current()) + 1

	async def get_last_counted(self) -> Optional[int]:
		return (await execute_get('SELECT last_user_id FROM game_state'))[0][0]

	async def set_last_counted(self, value: Optional[int]) -> None:
		await execute_write('UPDATE game_state SET last_user_id = %s', (value,))

	async def get_response(self, message: Message) -> Response:
		user_input: str = message.content.lower().strip()
		author_id: int = message.author.id

		for key, value in REPLACEMENT_SYMBOLS.items():
			user_input = user_input.replace(key, f' {value} ')

		if not all(character in SUPPORTED_CHARACTERS for character in user_input):
			return Response()

		if not await execute_get('SELECT * FROM users WHERE user_id = %s', (author_id,)):
			await execute_write(
				'INSERT INTO users (user_id, correct_count, incorrect_count, max_count) VALUES (%s, %s, %s, %s)',
				(author_id, 0, 0, 0)
			)

		try:
			result: int = round(eval(user_input))
		except (SyntaxError, ValueError, TypeError):
			return Response()
		except ZeroDivisionError:
			return Response('You can\'t divide by **0**!', zero_division=True)

		if await self.get_last_counted() == author_id:
			await self.lose(author_id)
			return Response(
				f'**Incorrect**, {message.author.mention}! You can\'t count twice in a row! The next number is **1**!',
				is_number=True, is_valid_number=False
			)

		if result == await self.get_next():
			await self.set_current(await self.get_current() + 1)
			await execute_write('UPDATE users SET correct_count = correct_count + 1 WHERE user_id = %s', (author_id,))
			await self.set_last_counted(author_id)

			if (new_count := await self.get_current()) > (await execute_get('SELECT max_count FROM users WHERE user_id = %s', (author_id,)))[0][0]:
				await execute_write('UPDATE users SET max_count = %s WHERE user_id = %s', (new_count, author_id))

			return Response(None, True, True)
		else:
			await self.lose(author_id)
			return Response(f'**Incorrect**, {message.author.mention}! The next number is **1**!', True, False)

	async def lose(self, author_id: int) -> None:
		await self.set_current(0)
		await self.set_last_counted(0)
		await execute_write('UPDATE users SET incorrect_count = incorrect_count + 1 WHERE user_id = %s', (author_id,))

	async def get_leaderboard(self, order: str) -> str:
		users = await execute_get(
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

	async def get_user_stats(self, user_id: int) -> str:
		response = await execute_get(
			'SELECT correct_count, incorrect_count, max_count, accuracy FROM users WHERE user_id = %s',
			(user_id,)
		)

		if not response:
			return 'No data on the user :('

		correct, incorrect, max_count, accuracy = response[0]

		return (f':white_check_mark: Correct: **{correct}**\n'
		        f':x: Incorrect: **{incorrect}**\n'
		        f':trophy: Max count: **{max_count}**\n'
		        f':dart: Accuracy: **{accuracy:,.1%}**')


message_handler: MessageHandler = MessageHandler()
