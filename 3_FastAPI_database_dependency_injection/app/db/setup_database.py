import sqlite3

def setup():
	connection = sqlite3.connect("./app/db/database.db")
	cursor = connection.cursor()
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS books
		(
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			book_name TEXT,
			book_author TEXT
		)
		""")
	connection.commit()
	connection.close()
