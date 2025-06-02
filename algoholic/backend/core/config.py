import os
from dotenv import load_dotenv

from pathlib import Path
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
	PROJECT_NAME: str = "Job Board"
	PROJECT_VERSION: str = "1.0.0"

	POSTGRES_USER: str = os.getenv("POSTGRES_USER")		#getting the value of the POSTGRES_USER environment variable.
	POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
	POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER","localhost")		# Try to get the environment variable POSTGRES_SERVER. # If it's not set, use "localhost" as the default value.
	POSTGRES_PORT:str = os.getenv("POSTGRES_PORT",5432)	#default postgres
	POSTGRES_DB: str = os.getenv("POSTGRES_DB","tdd")
	DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

settings = Settings()



