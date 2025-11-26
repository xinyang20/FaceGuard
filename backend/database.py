"""
Database models and connection management using SQLAlchemy.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from utils.logger import get_logger

logger = get_logger(__name__)

# Database configuration
DATABASE_URL = "sqlite:///./access_control.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class User(Base):
    """User model - stores registered users and their face features."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    feature_vector = Column(Text, nullable=False)  # JSON string of 512-dim vector
    avatar_path = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AccessLog(Base):
    """Access log model - records all recognition attempts."""
    __tablename__ = "access_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for strangers
    user_name = Column(String(100), nullable=False)  # "Unknown" for strangers
    status = Column(String(20), nullable=False)  # PASS, REJECT, NO_FACE
    confidence = Column(Float, nullable=True)
    snapshot_path = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class SystemConfig(Base):
    """System configuration model - key-value pairs."""
    __tablename__ = "system_config"
    
    key = Column(String(100), primary_key=True)
    value = Column(String(255), nullable=False)


def init_database():
    """Initialize database tables and default configuration."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize default config if not exists
    db = SessionLocal()
    try:
        # Check if config exists
        existing_config = db.query(SystemConfig).first()
        if not existing_config:
            # Add default configuration
            default_configs = [
                SystemConfig(key="frame_interval_ms", value="500"),
                SystemConfig(key="recognition_threshold", value="0.5"),
            ]
            db.add_all(default_configs)
            db.commit()
            logger.info("Default configuration initialized")
    finally:
        db.close()


def get_db() -> Session:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
