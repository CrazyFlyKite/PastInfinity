import logging

from discord import Intents, Message, Interaction, User, CustomActivity, Status, Colour, Forbidden
from discord.app_commands import checks, choices, command, guild_only, Group, AppCommandError, MissingRole, \
	MissingAnyRole, NoPrivateMessage
from discord.ext.commands import Bot

from database import execute_get, execute_write
from decorators import log_command, limit_command
from embeds import embed, success_embed, error_embed
from message_handler import message_handler
from setup_logging import setup_logging
from utilities import *

# Setup logging
if not IS_NAS:
	setup_logging(level=logging.DEBUG, logging_format=LOGGING_FORMAT)
else:
	logging.basicConfig(level=logging.DEBUG, format=LOGGING_FORMAT)

# Setup Bot
intents: Intents = Intents.default()
intents.message_content = True  # NOQA
bot: Bot = Bot(command_prefix='/', intents=intents, activity=CustomActivity(name='Counting 💯'),
               status=Status.do_not_disturb)
bot.remove_command('help')


# Startup
@bot.event
async def on_ready() -> None:
	logging.info(f'@{bot.user.name} is now running!')
	logging.info(f'Commands synced: {', '.join(cmd.name for cmd in await bot.tree.sync())}')


@bot.tree.error
async def on_app_command_error(interaction: Interaction, error: AppCommandError):
	if isinstance(error, (MissingRole, MissingAnyRole)):
		await interaction.response.send_message(
			embed=error_embed('You don\'t have the required role to use this command!'),
			ephemeral=True
		)
	elif isinstance(error, NoPrivateMessage):
		await interaction.response.send_message(
			embed=error_embed('You can\'t use this command in private messages!'),
			ephemeral=True
		)
	else:
		logging.critical(f'Command Error: {error}')


# Commands
@bot.tree.command(name='info', description='Show information about the bot')
@log_command
async def info(interaction: Interaction) -> None:
	await interaction.response.send_message(embed=embed(INFORMATION), ephemeral=True)


@bot.tree.command(name='next', description='Show the next number in the sequence')
@guild_only()
@limit_command
@log_command
async def next(interaction: Interaction) -> None:
	message: str = f'Next number: **{await message_handler.get_next()}**'

	if await message_handler.get_last_counted():
		message += f'\nThe last count was made by **<@{await message_handler.get_last_counted()}>**'

	await interaction.response.send_message(embed=embed(message), ephemeral=True)


@bot.tree.command(name='leaderboard', description=f'Display the Top users by the correct count, incorrect count, ect…')
@choices(order=LEADERBOARD_ORDER_CHOICES)
@guild_only()
@limit_command
@log_command
async def leaderboard(interaction: Interaction, order: Optional[str] = LEADERBOARD_ORDER_CHOICES[0].value) -> None:
	await interaction.response.send_message(
		embed=embed(
			title='The Leaderboard' + (f' | {order.replace('_', ' ').title()}' if order != 'correct_count' else ''),
			description=await message_handler.get_leaderboard(order),
			color=Colour.blue(),
			thumbnail='https://gdbrowser.com/assets/trophies/1.png'
		)
	)


@bot.tree.command(name='stats', description='Show user statistics')
@guild_only()
@limit_command
@log_command
async def stats(interaction: Interaction, user: Optional[User] = None) -> None:
	if user is None:
		user = interaction.user

	await interaction.response.send_message(
		embed=embed(
			title=f'Statistics of @{user.name}',
			description=await message_handler.get_user_stats(user.id),
			thumbnail=user.avatar.url
		)
	)


class SwitchGroup(Group, name='switch'):
	@command(name='channel', description='Change bot\'s operating channel to another')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@log_command
	async def channel(self, interaction: Interaction) -> None:
		old_channel: int = (await execute_get('SELECT channel_id FROM game_state'))[0][0]
		new_channel: int = interaction.channel.id

		if new_channel == old_channel:
			await interaction.response.send_message(embed=error_embed('I\'m already here…'), ephemeral=True)
			return

		if old_channel:
			await bot.get_channel(old_channel).send(embed=embed('I\'m leaving… I\'ve done all I can…'))

		await execute_write('UPDATE game_state SET channel_id = %s', (new_channel,))

		await interaction.response.send_message(
			embed=success_embed(f'Now I will count here! The next number is **{await message_handler.get_next()}**.')
		)


class BlacklistGroup(Group, name='blacklist'):
	@command(name='add', description='Add user to the blacklist')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@limit_command
	@log_command
	async def add(self, interaction: Interaction, user: User) -> None:
		if user.id == DEVELOPER_ID:
			return await interaction.response.send_message(
				embed=error_embed('You really think you can blacklist the **developer**?!'),
				ephemeral=True
			)

		response = await execute_get('SELECT is_blacklisted FROM users WHERE user_id = %s', (user.id,))
		already_blacklisted = response[0][0] if response else False

		if not already_blacklisted:
			await execute_write('''
			INSERT INTO users (user_id, is_blacklisted)
			VALUES (%s, TRUE)
			ON DUPLICATE KEY UPDATE is_blacklisted = TRUE
			''', (user.id,))

			await interaction.response.send_message(
				embed=success_embed(f'{user.mention} has been added to the blacklist!')
			)
		else:

			await interaction.response.send_message(
				embed=error_embed(f'{user.mention} is already in the blacklist!'),
				ephemeral=True
			)

	@command(name='remove', description='Remove user from the blacklist')
	@checks.has_any_role(*MODERATORS)
	@guild_only()
	@limit_command
	@log_command
	async def remove(self, interaction: Interaction, user: User) -> None:
		res = await execute_get('SELECT is_blacklisted FROM users WHERE user_id = %s', (user.id,))
		is_blacklisted = res[0][0] if res else False

		if is_blacklisted:
			await execute_write('UPDATE users SET is_blacklisted = FALSE WHERE user_id = %s', (user.id,))

			await interaction.response.send_message(
				embed=success_embed(f'{user.mention} has been removed from the blacklist!')
			)
		else:

			await interaction.response.send_message(
				embed=error_embed(f'{user.mention} is not in the blacklist!'),
				ephemeral=True
			)


# Handle messages
@bot.event
async def on_message(message: Message) -> None:
	channel_id: int = (await execute_get('SELECT channel_id FROM game_state'))[0][0]

	if message.author != bot.user and message.channel.id == channel_id:
		logging.debug(f'@{message.author} said \"{message.content}\" in {message.channel.name}.')

		if not (message.content or message.attachments or message.embeds or message.stickers):
			logging.critical('Message is empty.')
			return

		res = await execute_get('SELECT is_blacklisted FROM users WHERE user_id = %s', (message.author.id,))
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

		response: Response = await message_handler.get_response(message)

		try:
			if message.channel.id == channel_id:
				if response.zero_division:
					await message.channel.send(embed=error_embed(response.message))

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


# Main entry point
def main() -> None:
	bot.tree.add_command(SwitchGroup())
	bot.tree.add_command(BlacklistGroup())
	bot.run(TOKEN)


if __name__ == '__main__':
	main()
