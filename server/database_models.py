from pydantic import BaseModel, UUID4
from typing import Literal

class User(BaseModel):
    id: UUID4
    name: str
    
class Book(BaseModel):
    id: UUID4 | None = None
    author: str
    title: str
    issued_by: UUID4 | Literal[""]