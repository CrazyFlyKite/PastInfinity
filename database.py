from mysql.connector.pooling import MySQLConnectionPool

from utilities import *

pool: MySQLConnectionPool = MySQLConnectionPool(
	pool_name='pastinfinity',
	pool_size=10,
	host=HOST_IP,
	user=MYSQL_USER,
	password=MYSQL_PASSWORD,
	database=DATABASE
)


async def execute_get(code: str, parameters: Optional[Any] = None):
	connection = pool.get_connection()
	cursor = connection.cursor()

	try:
		cursor.execute(code, parameters)
		return cursor.fetchall()
	finally:
		cursor.close()
		connection.close()


async def execute_write(code: str, parameters: Optional[Any] = None):
	connection = pool.get_connection()
	cursor = connection.cursor()

	try:
		cursor.execute(code, parameters)
		connection.commit()
	finally:
		cursor.close()
		connection.close()
