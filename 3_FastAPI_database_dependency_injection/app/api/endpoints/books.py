from fastapi import APIRouter, Depends
from pydantic import BaseModel
import sqlite3
import json

from app.db.database_models import Book, BookDelete
from app.db.session import get_db

router = APIRouter()

@router.post("/create")
def create_item(data: Book,connection: sqlite3.Connection = Depends(get_db)):
	book_name = data.book_name	
	book_author = data.book_author
	cursor = connection.cursor()
	cursor.execute("INSERT INTO books (book_name,book_author) VALUES (?,?)",(book_name,book_author))
	connection.commit()
	return {"message":"Data added to database."}

@router.get("/retrieve")
def get_all_items(connection: sqlite3.Connection = Depends(get_db)):
	cursor = connection.cursor()
	cursor.execute("SELECT * FROM books")
	rows = cursor.fetchall()

	json_data = [] 	# list of dictionaries
	columns = ["id","book_name","book_author"]
	for row in rows:
		single_dict = dict(zip(columns,row))
		json_data.append(single_dict)		# add one more dictionary to list

	return json_data

@router.put("/update")
def update_item(data: Book,connection: sqlite3.Connection =  Depends(get_db)):
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

	return f"Book with id=({id}) updated with book_name=({book_name}) and book_author=({book_author})"

@router.delete("/delete")
def delete_item(data: BookDelete,connection: sqlite3.Connection = Depends(get_db)):
	cursor = connection.cursor()	
	id = data.id
	cursor.execute("""
		DELETE FROM books 
		WHERE id = ?	
		""",(id,))

	connection.commit()

	return f"Book with id=({id}) deleted."

@router.delete("/delete/{id}")
def delete_item(id: int,connection: sqlite3.Connection = Depends(get_db)):
	cursor = connection.cursor()	
	cursor.execute("""
		DELETE FROM books 
		WHERE id = ?	
		""",(id,))

	connection.commit()

	return f"Book with id=({id}) deleted."

