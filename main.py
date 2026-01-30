import logging

from discord import Intents, Message, Interaction, User, CustomActivity, Colour, Forbidden
from discord.app_commands import choices, command, Group
from discord.ext.commands import Bot

from database import execute_get, execute_write
from decorators import log_command, limit_command, trusted_roles_only
from embeds import embed, success_embed, error_embed
from message_handler import message_handler
from setup_logging import setup_logging
from utilities import *

# Setup logging
if not IS_NAS:
	setup_logging(level=logging.DEBUG, logging_format='[%(levelname)s]: %(message)s')

# Setup Bot
intents: Intents = Intents.default()
intents.message_content = True  # NOQA
bot: Bot = Bot(command_prefix='/', intents=intents)
bot.remove_command('help')


# Startup
@bot.event
async def on_ready() -> None:
	await bot.change_presence(activity=CustomActivity(name='Counting 💯'))
	logging.info(f'@{bot.user.name} is now running!')
	logging.info(f'Commands synced: {', '.join(cmd.name for cmd in await bot.tree.sync())}')


# Commands
@bot.tree.command(name='next', description='Show the next number in the sequence')
@log_command
@limit_command
async def next(interaction: Interaction) -> None:
	message: str = f'Next number: **{message_handler.next}**'

	if message_handler.last_counted:
		message += f'\nThe last count was made by **<@{message_handler.last_counted}>**'

	# noinspection PyUnresolvedReferences
	await interaction.response.send_message(embed=embed(message), ephemeral=True)


@bot.tree.command(name='info', description='Show information about the bot')
@log_command
async def info(interaction: Interaction) -> None:
	# noinspection PyUnresolvedReferences
	await interaction.response.send_message(embed=embed(INFORMATION), ephemeral=True)


@bot.tree.command(name='leaderboard', description=f'Display the Top users by the correct count, incorrect count, ect…')
@choices(order=LEADERBOARD_ORDER_CHOICES)
@log_command
@limit_command
async def leaderboard(interaction: Interaction, order: Optional[str] = LEADERBOARD_ORDER_CHOICES[0].value) -> None:
	# noinspection PyUnresolvedReferences
	await interaction.response.send_message(
		embed=embed(
			message_handler.get_leaderboard(order),
			Colour.blue(),
			f'The Leaderboard | {order.replace('_', ' ').title()}',
			'https://gdbrowser.com/assets/trophies/1.png'
		)
	)


@bot.tree.command(name='stats', description='Show user statistics')
@log_command
@limit_command
async def stats(interaction: Interaction, user: Optional[User] = None) -> None:
	if user is None:
		user = interaction.user

	# noinspection PyUnresolvedReferences
	await interaction.response.send_message(
		embed=embed(
			title=f'Statistics of @{user.name}',
			description=message_handler.get_user_stats(user.id),
			thumbnail=user.avatar.url
		)
	)


class SwitchGroup(Group, name='switch'):
	@command(name='channel', description='Change bot\'s operating channel to another')
	@log_command
	@trusted_roles_only(*TRUSTED_ROLES)
	async def channel(self, interaction: Interaction) -> None:
		old_channel: int = execute_get('SELECT channel_id FROM game_state')[0][0]
		new_channel: int = interaction.channel.id

		if new_channel == old_channel:
			# noinspection PyUnresolvedReferences
			await interaction.response.send_message(embed=error_embed('I\'m already here…'), ephemeral=True)
			return

		if old_channel:
			await bot.get_channel(old_channel).send(embed=embed('I\'m leaving… I\'ve done all I can…'))

		execute_write('UPDATE game_state SET channel_id = %s', (new_channel,))

		# noinspection PyUnresolvedReferences
		await interaction.response.send_message(
			embed=success_embed(f'Now I will count here! The next number is **{message_handler.next}**.')
		)


class BlacklistGroup(Group, name='blacklist'):
	@command(name='add', description='Add user to the blacklist')
	@log_command
	@limit_command
	@trusted_roles_only(*TRUSTED_ROLES)
	async def add(self, interaction: Interaction, user: User) -> None:
		if user.id == DEVELOPER_IP:
			# noinspection PyUnresolvedReferences
			return await interaction.response.send_message(
				embed=error_embed('You really think you can blacklist the **developer**?!'),
				ephemeral=True
			)

		response = execute_get('SELECT is_blacklisted FROM users WHERE user_id = %s', (user.id,))
		already_blacklisted = response[0][0] if response else False

		if not already_blacklisted:
			execute_write('''
			INSERT INTO users (user_id, is_blacklisted)
			VALUES (%s, TRUE)
			ON DUPLICATE KEY UPDATE is_blacklisted = TRUE
			''', (user.id,))

			# noinspection PyUnresolvedReferences
			await interaction.response.send_message(
				embed=success_embed(f'{user.mention} has been added to the blacklist!')
			)
		else:
			# noinspection PyUnresolvedReferences
			await interaction.response.send_message(
				embed=error_embed(f'{user.mention} is already in the blacklist!'),
				ephemeral=True
			)

	@command(name='remove', description='Remove user from the blacklist')
	@log_command
	@limit_command
	@trusted_roles_only(*TRUSTED_ROLES)
	async def remove(self, interaction: Interaction, user: User) -> None:
		res = execute_get('SELECT is_blacklisted FROM users WHERE user_id = %s', (user.id,))
		is_blacklisted = res[0][0] if res else False

		if is_blacklisted:
			execute_write('UPDATE users SET is_blacklisted = FALSE WHERE user_id = %s', (user.id,))

			# noinspection PyUnresolvedReferences
			await interaction.response.send_message(
				embed=success_embed(f'{user.mention} has been removed from the blacklist!')
			)
		else:
			# noinspection PyUnresolvedReferences
			await interaction.response.send_message(
				embed=error_embed(f'{user.mention} is not in the blacklist!'),
				ephemeral=True
			)


# Handle messages
@bot.event
async def on_message(message: Message) -> None:
	channel_id: int = execute_get('SELECT channel_id FROM game_state')[0][0]

	if message.author != bot.user and message.channel.id == channel_id:
		logging.debug(f'@{message.author} said \"{message.content}\" in {message.channel.name}.')

		if not message.content:
			logging.critical('Message is empty.')
			return

		res = execute_get('SELECT is_blacklisted FROM users WHERE user_id = %s', (message.author.id,))
		is_blacklisted = res[0][0] if res else False

		if is_blacklisted:
			await message.delete()
			try:
				await message.author.send(
					embed=error_embed('You\'ve been **blacklisted**, so you can\'t count anymore!')
				)
				return
			except Forbidden:
				pass

			return

		response: Response = message_handler.get_response(message)

		try:
			if message.channel.id == channel_id:
				if response.is_number:
					if response.is_valid_number:
						await message.add_reaction(CORRECT_EMOJI)

						if message.content.strip() == '69':
							await message.add_reaction(FIRE_EMOJI)
							await message.channel.send(
								embed=success_embed(f'Congrats, {message.author.mention}! You got the **69** :3')
							)
					else:
						await message.add_reaction(INCORRECT_EMOJI)
						await message.channel.send(embed=error_embed(response.message))
				else:
					if response.message is not None:
						await message.channel.send(response.message)
		except Exception as exception:
			logging.critical(exception)


# Assign main commands
bot.tree.add_command(SwitchGroup())
bot.tree.add_command(BlacklistGroup())


# Main entry point
def main() -> None:
	bot.run(TOKEN)


if __name__ == '__main__':
	main()
