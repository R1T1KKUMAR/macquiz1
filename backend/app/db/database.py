from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import os
from app.core.config import settings

# Create engine with appropriate settings for MySQL
# Remove SQLite-specific connect_args
connect_args = {}
if settings.DATABASE_URL.startswith('sqlite'):
    connect_args = {"check_same_thread": False}

engine_kwargs = {
    "connect_args": connect_args,
    "pool_pre_ping": True,  # Verify connections before using
    "pool_recycle": 3600,   # Recycle connections after 1 hour
    "echo": False,
}

# Disable connection pooling in serverless environments to avoid stale connections.
# Render runs a long-lived web service, so pooling is fine.
if os.getenv('VERCEL') or os.getenv('SERVERLESS'):
    engine_kwargs["poolclass"] = NullPool

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
