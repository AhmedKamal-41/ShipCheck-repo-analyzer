from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import DATABASE_URL, TESTING

# Use SQLite in-memory for unit tests (fast, no setup)
# Use Postgres for integration tests and production
if TESTING and "sqlite" in DATABASE_URL.lower():
    # Already using SQLite (test mode)
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
