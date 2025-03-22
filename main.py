import logging

from discord import Intents, Message, Interaction, User
from discord.app_commands import AppCommand
from discord.ext.commands import Bot

from data_manager import data_manager
from decorators import log_command, limit_command, trusted_roles_only
from emails import send_email
from message_handler import MessageHandler
from setup_logging import setup_logging
from utilities import *

# Setup logging
setup_logging(level=logging.DEBUG, logging_format='[%(levelname)s]: %(message)s')

# Setup Bot
intents: Intents = Intents.default()
intents.message_content = True  # NOQA
bot: Bot = Bot(command_prefix=COMMAND_PREFIX, intents=intents)
bot.remove_command('help')
message_handler: MessageHandler = MessageHandler()
channel_id: int = data_manager.load().get('channel')


# Message functionality
async def send_message(message: Message) -> None:
	if not message.content:
		logging.critical('Message is empty.')
		return

	message_handler.check_for_accuracy(message.author.id, message_handler.leaderboard.get(str(message.author.id)))

	if message.author.id in message_handler.super_blacklist:
		await message.delete()
		await message.author.send(embed=critical_embed('You can\'t count anymore! And I don\'t feel sorry because'
		                                               'you\'ve been **super-blacklisted**! That means that there\'s'
		                                               'no way back ;)'))
		return

	if message.author.id in message_handler.blacklist:
		await message.delete()
		await message.author.send(
			embed=error_embed('You\'ve been **blacklisted** because your accuracy is less than **40%**.')
		)
		return

	response: Response = message_handler.get_response(message)

	try:
		if message.channel.id == channel_id:
			if response.is_number:
				if response.is_valid_number:
					await message.add_reaction(CORRECT_EMOJI)

					if int(message.content) == 69:
						await message.add_reaction(FIRE_EMOJI)
						await message.add_reaction(HEART_EMOJI)
						await message.channel.send(
							embed=success_embed(f'Congrats, {message.author.mention}! You got the **69**!')
						)
				else:
					await message.add_reaction(INCORRECT_EMOJI)
					await message.channel.send(embed=error_embed(response.message))
			else:
				if response.message is not None:
					await message.channel.send(response.message)
	except Exception as exception:
		logging.critical(exception)


# Handle commands
@bot.tree.command(name='next', description='Shows the next number in the sequence')
@log_command
@limit_command(channel_id)
async def next(interaction: Interaction) -> None:
	message: str = f'Next number: **{message_handler.next}**'
	if message_handler.last_counted is not None:
		message += f'\nThe last count was made by **<@{message_handler.last_counted}>**'

	await interaction.response.send_message(embed=embed(message), ephemeral=True)


@bot.tree.command(name='info', description='Shows information about the bot and its functions')
@log_command
async def info(interaction: Interaction) -> None:
	await interaction.response.send_message(INFORMATION_MESSAGE, ephemeral=True)  # NOQA


@bot.tree.command(name='leaderboard', description='Displays the leaderboard of users by the number of correct numbers')
@log_command
@limit_command(channel_id)
async def leaderboard(interaction: Interaction) -> None:
	await interaction.response.send_message(
		embed=embed(message_handler.get_leaderboard(), Colour.blue(), 'The Leaderboard',
		            'https://gdbrowser.com/assets/trophies/1.png'))


@bot.tree.command(name='user_stats', description='Shows the user\'s statistics')
@log_command
@limit_command(channel_id)
async def user_stats(interaction: Interaction, user: Optional[User] = None) -> None:
	if user is None:
		user = interaction.user

	await interaction.response.send_message(
		embed=embed(title=f'Statistics of @{user.name}', description=message_handler.get_user_stats(user.id),
		            thumbnail=user.avatar.url)
	)


@bot.tree.command(name='switch_channel', description='Changes the channel for the bot to another')
@log_command
@trusted_roles_only(*TRUSTED_ROLES)
async def switch_channel(interaction: Interaction) -> None:
	global channel_id

	if interaction.channel.id == channel_id:
		await interaction.response.send_message(embed=error_embed('I\'m already here…'), ephemeral=True)
	else:
		await bot.get_channel(channel_id).send(embed=embed('I\'m leaving… I\'ve done all I can…'))
		channel_id = interaction.channel.id
		message_handler.last_counted = None
		await interaction.response.send_message(
			embed=success_embed(f'Now I will count here! The next number is **{message_handler.next}**.'))


@bot.tree.command(name='bake', description='Saves all data about the bot')
@log_command
@limit_command(channel_id)
@trusted_roles_only(*GODLY_ROLES)
async def bake(interaction: Interaction) -> None:
	data_manager.write('current', message_handler.current)
	data_manager.write('last_counted', message_handler.last_counted)
	data_manager.write('channel', channel_id)
	data_manager.write('leaderboard', data_manager.load().get('leaderboard') | message_handler.leaderboard)
	data_manager.write('blacklist', message_handler.blacklist)
	data_manager.write('super_blacklist', message_handler.super_blacklist)

	send_email(EMAIL, PASSWORD, subject='PastInfinity\'s data has been baked! Here\'s data.json', content='',
	           attachment='data.json')

	await interaction.response.send_message('All data saved!', ephemeral=True)


@bot.tree.command(name='blacklist_add', description='Adds user to the blacklist')
@log_command
@limit_command(channel_id)
@trusted_roles_only(*TRUSTED_ROLES)
async def blacklist_add(interaction: Interaction, user: User) -> None:
	if user.id not in message_handler.blacklist:
		if user.id == AUTHOR:
			await interaction.response.send_message('You can\'t blacklist the **great developer**!')
		else:
			message_handler.blacklist.append(user.id)
			await interaction.response.send_message(
				embed=success_embed(f'{user.mention} has been added to the blacklist!'))
	else:
		await interaction.response.send_message(embed=error_embed(f'{user.mention} is already in the blacklist!'),
		                                        ephemeral=True)


@bot.tree.command(name='blacklist_remove', description='Removes user from the blacklist')
@log_command
@limit_command(channel_id)
@trusted_roles_only(*TRUSTED_ROLES)
async def blacklist_remove(interaction: Interaction, user: User) -> None:
	if user.id in message_handler.blacklist:
		message_handler.blacklist.remove(user.id)
		await interaction.response.send_message(
			embed=success_embed(f'{user.mention} has been removed from the blacklist!'))
	else:
		await interaction.response.send_message(embed=error_embed(f'{user.mention} is not in the blacklist!'),
		                                        ephemeral=True)


# Handle startup for the discloud.config
@bot.event
async def on_ready() -> None:
	logging.info(f'{bot.user.name} is now running!')
	synced_commands: List[AppCommand] = await bot.tree.sync()
	logging.info(f"Synced {len(synced_commands)} commands: {', '.join(command.name for command in synced_commands)}")


# Handle incoming messages
@bot.event
async def on_message(message: Message) -> None:
	if message.author != bot.user and message.channel.id == channel_id:
		logging.debug(f'@{message.author} said \"{message.content}\" in {message.channel.name}.')
		await send_message(message)


# Main entry point
def main() -> None:
	bot.run(TOKEN)


if __name__ == '__main__':
	main()
