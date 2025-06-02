from fastapi import FastAPI
from app.api.endpoints import books
from app.db.setup_database import setup
	
app = FastAPI()
app.include_router(books.router,prefix="/books")
setup()

@app.get("/")
def read_root():
	return "Hello, CRUD application. Database loaded."

