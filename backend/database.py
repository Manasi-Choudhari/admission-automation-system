# database.py - SQLite database connection and session management

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite database file will be created in the backend folder
DATABASE_URL = "sqlite:///./admissions.db"

# Create the SQLAlchemy engine
# connect_args is needed for SQLite to allow multi-threaded access
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# SessionLocal is a factory for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
Base = declarative_base()


def get_db():
    """
    Dependency function that provides a database session.
    Used with FastAPI's Depends() to inject DB sessions into routes.
    Automatically closes the session after the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
