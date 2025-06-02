from fastapi import FastAPI, status
from database import DBBook
from database_models import Book
from pydantic import UUID4

app = FastAPI()

@app.get('/')
def read_root():
    return "Hello World!"


@app.get('/books')
def read_all_books():
    return DBBook.read_book()

@app.get('/books/{id}')
def read_book_by_id(id: UUID4):
    return DBBook.read_book(str(id))

@app.post('/books', status_code=status.HTTP_201_CREATED)
def create_book(book: Book):
    return DBBook.create_book(book)

@app.post('/books/{id}')
def update_book(id: str, book: Book):
    book.id = id
    return DBBook.update_book(book)

@app.delete('/books/{id}')
def delete_book(id: str):
    return DBBook.delete_book(id)