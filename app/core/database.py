"""
Database configuration using SQLAlchemy 2.0 style.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings


# Create engine
engine = create_engine(settings.DATABASE_URL, echo=True)


# Base class for models
class Base(DeclarativeBase):
    pass


# Session factory
SessionLocal = sessionmaker(bind=engine)