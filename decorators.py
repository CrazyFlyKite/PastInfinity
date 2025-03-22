import logging
from functools import wraps
from typing import Callable

from discord import Interaction


def log_command(command: Callable) -> Callable:
	"""
	Decorator for logging commands.

	This decorator logs the usage of a command in the console.
	"""

	@wraps(command)
	async def wrapper(*args, **kwargs) -> None:
		interaction: Interaction = args[0]

		logging.debug(
			f'@{interaction.user.name} used the \"/{command.__name__}\" command in {interaction.channel.name}.'
		)

		await command(*args, **kwargs)

	return wrapper


def limit_command(channel_id: int) -> Callable:
	"""
	Decorator for limiting commands to specific channels.

	This decorator restricts the usage of a command to specified channels.
	"""

	def decorator(command: Callable) -> Callable:
		@wraps(command)
		async def wrapper(*args, **kwargs) -> None:
			interaction: Interaction = args[0]

			if interaction.channel.id == channel_id:
				await command(*args, **kwargs)
			else:
				await interaction.response.send_message(  # NOQA
					'You cannot use my commands in this channel.',
					ephemeral=True
				)

		return wrapper

	return decorator


def trusted_roles_only(*roles: str) -> Callable:
	"""
	Decorator for restricting commands to trusted users.

	This decorator allows only users with specified roles to use the command.
	"""

	def decorator(command: Callable) -> Callable:
		@wraps(command)
		async def wrapper(*args, **kwargs) -> None:
			interaction: Interaction = args[0]

			if any([role.name in roles for role in interaction.user.roles]):
				await command(*args, **kwargs)
			else:
				trusted_roles: str = ', '.join(f'**{role}**' for role in roles)
				await interaction.response.send_message(  # NOQA
					f'This command can only be used by users with roles: {trusted_roles}.',
					ephemeral=True
				)

		return wrapper

	return decorator
