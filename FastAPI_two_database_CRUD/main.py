from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import json
from pydantic import BaseModel
from typing import Optional

data_structure = {}
	
def setup():
	connection = sqlite3.connect("database.db")
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
	
class Book(BaseModel):
	id: Optional[int] = None
	book_name: str
	book_author: str

class BookDelete(BaseModel):
	id: int

app = FastAPI()
setup()

@app.get("/")
def read_root():
	return "Hello, CRUD application. Database loaded. "

@app.post("/create")
def create_item(data: Book):
	connection = sqlite3.connect("database.db")
	book_name = data.book_name	
	book_author = data.book_author
	cursor = connection.cursor()
	cursor.execute("INSERT INTO books (book_name,book_author) VALUES (?,?)",(book_name,book_author))
	connection.commit()
	connection.close()
	return {"message":"Data added to database."}

@app.get("/retrieve")
def get_all_items():
	connection = sqlite3.connect("database.db")
	cursor = connection.cursor()
	cursor.execute("SELECT * FROM books")
	rows = cursor.fetchall()

	json_data = [] 	# list of dictionaries
	columns = ["id","book_name","book_author"]
	for row in rows:
		single_dict = dict(zip(columns,row))
		json_data.append(single_dict)		# add one more dictionary to list
	connection.close()

	return json_data

@app.put("/update")
def update_item(data: Book):
	connection = sqlite3.connect("database.db")
	cursor = connection.cursor()	
	id = data.id
	book_name = data.book_name
	book_author = data.book_author
	cursor.execute("""
		UPDATE books 
		SET book_name = ?,book_author = ?
		WHERE id = ?	
		""",(book_name,book_author,id))

	connection.commit()
	cursor.execute("SELECT * FROM books WHERE id = ?",(id,))	# adding trailing makes it into a list
	row = cursor.fetchone()
	connection.close()

	return f"Book with id=({id}) updated with book_name=({book_name}) and book_author=({book_author})"

@app.delete("/delete")
def delete_item(data: BookDelete ):
	connection = sqlite3.connect("database.db")
	cursor = connection.cursor()	
	id = data.id
	cursor.execute("""
		DELETE FROM books 
		WHERE id = ?	
		""",(id,))

	connection.commit()
	connection.close()

	return f"Book with id=({id}) deleted."

@app.delete("/delete/{id}")
def delete_item(id: int):
	connection = sqlite3.connect("database.db")
	cursor = connection.cursor()	
	cursor.execute("""
		DELETE FROM books 
		WHERE id = ?	
		""",(id,))

	connection.commit()
	connection.close()

	return f"Book with id=({id}) deleted."

