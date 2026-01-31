# PastInfinity

### Requirements

![Python Version](https://img.shields.io/badge/Python-3.14%2B-blue)

![discord](https://img.shields.io/badge/discord-2.3.2%2B-blue)
![mysql-connector-python](https://img.shields.io/badge/mysql-9.2.0%2B-red)
![python-dotenv](https://img.shields.io/badge/dotenv-1.0.0%2B-green)

## Introduction

**PastInfinity** is a Discord bot for keeping track of a sequence of numbers in a specific.

## File Structure

- [`main.py`](main.py) - Main entry point containing all the bot commands
- [`message_handler.py`](message_handler.py) - Processing incoming message
- [`decorators.py`](decorators.py) - Wrapper functions for commands
- [`database.py`](database.py) - Functions database interactions
- [`embeds.py`](embeds.py) - Custom embed templates for Discord messages
- [`utilities.py`](utilities.py) - Constants and platform detection
- [`setup_logging.py`](setup_logging.py) - Enhanced terminal logging

## Host

`docker-compose.yml` and `Dockerfile` are there, because the bot hosted on a Synology NAS, so `utilities.py` has some
platform detection functionality.

## .env

This project requires `.env` file which looks like this:

```dotenv
TOKEN=???
MYSQL_USER=???
MYSQL_PASSWORD=???
SYNOLOGY_IP=???.???.?.??
```

## Commands

Detailed command documentation can be found in [`config/info_template.md`](config/info_template.md)

## Contact

- [Discord](https://discord.com/users/873920068571000833)
- [GitHub](https://github.com/CrazyFlyKite)
- [Email](mailto:karpenkoartem2846@gmail.com)
