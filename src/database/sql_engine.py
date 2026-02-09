import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from contextlib import contextmanager

from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

db_url = os.getenv("DATABASE_URL")
engine = create_engine(db_url)
Base = declarative_base()
Session = sessionmaker(bind=engine)

@contextmanager
def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()
