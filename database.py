import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import bcrypt
from models import Base

DATABASE_URL = "sqlite:///./lms.db"

# Create Database Engine
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create all tables in the SQLite database."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency for FastAPI route handlers to get a db session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Password Hashing Helper Utilities (Direct bcrypt calls to avoid passlib bugs in Python 3.12+)
def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False

