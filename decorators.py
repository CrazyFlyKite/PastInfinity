import logging
from functools import wraps
from typing import Callable

from discord import Interaction

from database import execute_get
from embeds import error_embed


def log_command(command: Callable) -> Callable:
	@wraps(command)
	async def wrapper(*args, **kwargs) -> None:
		try:
			interaction: Interaction = args[1]
		except IndexError:
			interaction: Interaction = args[0]

		logging.debug(f'@{interaction.user.name} used the \"/{interaction.command.qualified_name}\" command in {interaction.channel.name}.')

		await command(*args, **kwargs)

	return wrapper


def limit_command(command: Callable) -> Callable:
	@wraps(command)
	async def wrapper(*args, **kwargs) -> None:
		try:
			interaction: Interaction = args[1]
		except IndexError:
			interaction: Interaction = args[0]

		if interaction.channel.id == (await execute_get('SELECT channel_id FROM game_state'))[0][0]:
			await command(*args, **kwargs)
		else:
			# noinspection PyUnresolvedReferences
			await interaction.response.send_message(
				embed=error_embed('You cannot use my commands in this channel!'),
				ephemeral=True
			)

	return wrapper
