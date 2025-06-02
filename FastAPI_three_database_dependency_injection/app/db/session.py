# calling this function returns a session of database

import sqlite3
from typing import Generator

def get_db() -> Generator:
	connection = sqlite3.connect("./app/db/database.db")
	try:
		yield connection
	finally:
		connection.close()


