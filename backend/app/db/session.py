"""
app/db/session.py
Database connection engine, sessionmaker, and dependency for SQLite.
"""
import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_FILE = BASE_DIR / getattr(settings, "DB_NAME", "zerowaste.db")

# Connect to database using SQLite with multithreading support for FastAPI
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    db_file_str = getattr(settings, "DB_NAME", "zerowaste.db")
    db_path = BASE_DIR / db_file_str if not Path(db_file_str).is_absolute() else Path(db_file_str)
    DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a SQLAlchemy database session and ensures clean closure.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
