import sqlite3
from database_models import Book, User
from uuid import uuid4

def setup():
    with sqlite3.connect("database.db") as connection:
        cursor = connection.cursor()
        cursor.execute("DROP TABLE IF EXISTS users;")
        cursor.execute("DROP TABLE IF EXISTS books;")
        connection.commit()
        
        cursor.execute("CREATE TABLE users (id UUID PRIMARY KEY, name TEXT);")
        cursor.execute("CREATE TABLE books (id UUID PRIMARY KEY, title TEXT, author TEXT, issued_by UUID, FOREIGN KEY(issued_by) REFERENCES users(id))")
        connection.commit()
        
        cursor.execute("INSERT INTO users VALUES ('347da0c3-2c72-4bf9-bbb4-4111d6dc9140', '<LOCKED>')")
        connection.commit()
        
        cursor.execute("""INSERT INTO users (id, name) VALUES ('517b25d3-cf3b-43ed-b711-47fe1f885aa8', 'Paras Shrote'),('f5af7637-211b-4f2f-a7fd-b42d73ad6a3f', 'Dev Parapalli');""")
        cursor.execute("INSERT INTO books (id,author,title,issued_by) VALUES ('01104a7f-174d-4763-a09a-e80661454320', 'Author A', 'Book A', ''),('6473e334-e0fe-4c08-98bb-56dae5d64c82', 'Author A', 'Book B', '');")
        connection.commit()


class DBBook():
    
    def create_book(book: Book):
        with sqlite3.connect("database.db") as connection:
            cursor = connection.cursor()
            id = uuid4()
            cursor.execute(f"INSERT INTO books VALUES ('{id}', '{book.title}', '{book.author}', '{book.issued_by}')")
            connection.commit()
            return str(id)
    
    def read_book(id: str | None = None):
        with sqlite3.connect("database.db") as connection:
            cursor = connection.cursor()
            if isinstance(id, str):
                res = cursor.execute(f"SELECT * from books WHERE books.id = '{id}';")
            else:
                res = cursor.execute("SELECT * from books;")
            # return [Book(id=x[0], title=x[1], author=x[2], issued_by=x[3]) for x in res.fetchall() ]
            return [Book(id=res[0], title=res[1], author=res[2], issued_by=res[3])]

    
    def update_book(book: Book):
        with sqlite3.connect("database.db") as connection:
            cursor = connection.cursor()
            id = book.id
            res = cursor.execute(f"UPDATE books SET title = '{book.title}', author = '{book.author}', issued_by = '{book.issued_by}' WHERE id = '{id}' ")
            connection.commit()
        
    def delete_book(b: str | Book | None = None):
        with sqlite3.connect("database.db") as connection:
            cursor = connection.cursor()
            if not b:
                raise ValueError("b MUST be UUID or database_models.Book")
            
            if not isinstance(b, str):
                b = b.id
            
            res = cursor.execute(f"SELECT * from books where id = '{b}';")
            data = res.fetchall()
            cursor.execute(f"DELETE FROM books where id = '{b}'")
            connection.commit()
            return data
        
        
         

if __name__ == "__main__":
    # setup()
    DBBook.read_book('01104a7f-174d-4763-a09a-e80661454320')
    
    