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

		logging.debug(
			f'@{interaction.user.name} used the \"/{command.__name__}\" command in {interaction.channel.name}.'
		)

		await command(*args, **kwargs)

	return wrapper


def limit_command(command: Callable) -> Callable:
	@wraps(command)
	async def wrapper(*args, **kwargs) -> None:
		try:
			interaction: Interaction = args[1]
		except IndexError:
			interaction: Interaction = args[0]

		if interaction.channel.id == execute_get('SELECT channel_id FROM game_state')[0][0]:
			await command(*args, **kwargs)
		else:
			# noinspection PyUnresolvedReferences
			await interaction.response.send_message(
				embed=error_embed('You cannot use my commands in this channel!'),
				ephemeral=True
			)

	return wrapper


def trusted_roles_only(*roles: str) -> Callable:
	def decorator(command: Callable) -> Callable:
		@wraps(command)
		async def wrapper(*args, **kwargs) -> None:
			try:
				interaction: Interaction = args[1]
			except IndexError:
				interaction: Interaction = args[0]

			if any([role.name in roles for role in interaction.user.roles]):
				await command(*args, **kwargs)
			else:
				trusted_roles: str = ', '.join(f'**{role}**' for role in roles)
				# noinspection PyUnresolvedReferences
				await interaction.response.send_message(
					embed=error_embed(f'This command can only be used by users with roles: {trusted_roles}!'),
					ephemeral=True
				)

		return wrapper

	return decorator
