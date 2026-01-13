from venv import create
from sqlalchemy import create_engine
from squlalchemy.orm import sessionmaker


db_url = "postgresql://postgres:1345678@localhost:5432/test.db"
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)