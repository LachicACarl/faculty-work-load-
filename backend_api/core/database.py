"""Database connection and session management."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from typing import Generator

from backend_api.core.config import settings

# Create database engine
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite configuration for local development
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL configuration for production
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for ORM models
Base = declarative_base()


def get_db() -> Generator:
    """Dependency for database session injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    # Import models to register them with Base
    from backend_api.models import (
        Faculty, Qualification, Availability,
        Subject, Section, WorkloadPolicy, Allocation
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print(f"✓ Database tables created/verified at {settings.DATABASE_URL}")
