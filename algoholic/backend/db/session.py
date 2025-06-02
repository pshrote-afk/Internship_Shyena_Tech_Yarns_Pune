from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings

# SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
# print("Database URL is: ",SQLALCHEMY_DATABASE_URL)
# engine = create_engine(SQLALCHEMY_DATABASE_URL)

SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app/db"
print("Database URL is: ",SQLALCHEMY_DATABASE_URL)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)








