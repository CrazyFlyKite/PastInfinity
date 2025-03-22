import logging
from typing import Dict


class ColoredFormatter(logging.Formatter):
	def format(self, record: logging.LogRecord) -> str:
		colors: Dict[int, str] = {
			logging.DEBUG: '\033[37m',  # White
			logging.INFO: '\033[34m',  # Blue
			logging.WARNING: '\033[33m',  # Yellow
			logging.ERROR: '\033[31m',  # Red
			logging.CRITICAL: '\033[1;31m'  # Bold Red
		}
		record.log_color = colors.get(record.levelno, '\033[0m')

		return super().format(record)


def setup_logging(level: int, logging_format: str) -> None:
	# Setup StreamHandler
	handler = logging.StreamHandler()
	handler.setFormatter(ColoredFormatter(f'%(log_color)s{logging_format}\033[0m'))

	# Basic configuration of logging, setting the level and handler
	logging.basicConfig(level=level, handlers=[handler])
