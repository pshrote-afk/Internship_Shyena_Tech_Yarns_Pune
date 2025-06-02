from pydantic import BaseModel
from typing import Optional

class Book(BaseModel):
	id: Optional[int] = None
	book_name: str
	book_author: str

class BookDelete(BaseModel):
	id: int