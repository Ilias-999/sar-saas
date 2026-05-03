import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://sar_user:sar_password@postgres:5432/sar_db"
)

# Create engine with connection pooling and retry logic
engine = create_engine(
    DATABASE_URL,
    echo=False,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Test connections before using them
    connect_args={
        "connect_timeout": 10,
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables with retry logic"""
    max_retries = 5
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            print("Database tables initialized successfully")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Failed to initialize database (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to initialize database after {max_retries} attempts")
                raise
