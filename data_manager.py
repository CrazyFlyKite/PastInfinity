import json
import logging
from os import path
from typing import Any

from utilities import PathLikeString, JSONDictionary


class DataManager:
	def __init__(self, data_file: PathLikeString) -> None:
		self._data_file = path.join(path.dirname(path.abspath(__file__)), data_file)

	@property
	def data_file(self) -> PathLikeString:
		return self._data_file

	def load(self) -> JSONDictionary:
		try:
			with open(self.data_file, 'r', encoding='utf-8') as file:
				return json.load(file)
		except (FileNotFoundError, IsADirectoryError):
			logging.critical(f'File {self.data_file} doesn\'t exist')
			exit()
		except PermissionError:
			logging.critical(f'Cannot access {self.data_file}')
			exit()

	def write(self, key: str, value: Any) -> None:
		data: JSONDictionary = self.load()
		data[key] = value

		with open(self.data_file, 'w', encoding='utf-8') as file:
			json.dump(data, file, indent='\t')


data_manager: DataManager = DataManager('data.json')
