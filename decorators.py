import logging
from functools import wraps
from typing import Callable

from discord import Interaction

from database import execute_get
from embeds import error_embed

from utilities import DEVELOPER_ID


def log_command(command: Callable) -> Callable:
	@wraps(command)
	async def wrapper(*args, **kwargs) -> None:
		interaction: Interaction = args[1] if len(args) > 1 else args[0]

		channel_name: str = interaction.channel.name if interaction.guild else 'Direct Messages'
		logging.debug(f'@{interaction.user.name} used the \"/{interaction.command.qualified_name}\" command in {channel_name}.')

		await command(*args, **kwargs)

	return wrapper


def limit_command(command: Callable) -> Callable:
	@wraps(command)
	async def wrapper(*args, **kwargs) -> None:
		interaction: Interaction = args[1] if len(args) > 1 else args[0]

		if interaction.channel.id == (await execute_get('SELECT channel_id FROM game_state'))[0][0]:
			await command(*args, **kwargs)
		else:
			await interaction.response.send_message(embed=error_embed('You cannot use my commands in this channel!'), ephemeral=True)

	return wrapper

def restrict_command(command) -> Callable:
	@wraps(command)
	async def wrapper(*args, **kwargs) -> None:
		interaction = args[1] if len(args) > 1 else args[0]

		if interaction.user.id == DEVELOPER_ID:
			return await command(*args, **kwargs)

		role_id = (await execute_get('SELECT moderator_role_id FROM game_state'))[0][0]

		if role_id and any(r.id == role_id for r in interaction.user.roles):
			return await command(*args, **kwargs)

		return await interaction.response.send_message(embed=error_embed('You have no permissions to use this command!'), ephemeral=True)

	return wrapper
