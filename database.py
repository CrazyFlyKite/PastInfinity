from typing import Tuple, Any

import mysql.connector

from utilities import *


def execute_get(code: str, parameters: Tuple = None) -> Any:
	connection = mysql.connector.connect(host=HOST_IP, user=MYSQL_USER, passwd=MYSQL_PASSWORD, database=DATABASE)
	cursor = connection.cursor()

	try:
		cursor.execute(code, parameters)
		return cursor.fetchall()
	finally:
		cursor.close()
		connection.close()


def execute_write(code: str, parameters: Tuple = None) -> None:
	connection = mysql.connector.connect(host=HOST_IP, user=MYSQL_USER, passwd=MYSQL_PASSWORD, database=DATABASE)
	cursor = connection.cursor()

	try:
		cursor.execute(code, parameters)
		connection.commit()
	finally:
		cursor.close()
		connection.close()
