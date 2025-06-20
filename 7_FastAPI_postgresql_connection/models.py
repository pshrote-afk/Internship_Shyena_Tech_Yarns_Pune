from sqlalchemy import column, integer, string
from database import Base

class Book(Base):
	__tablename__ = "books"

book_id = Column(Integer, primary_key = True, index = True, autoincrement = True)
book_name = Column(String, nullable = False)
book_author = Column(String, nullable = False)
issued_by = Column(String, nullable = True)
