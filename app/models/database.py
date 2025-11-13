"""
Database models for AI Video Generator Bot.

Uses PostgreSQL with SQLAlchemy ORM.
Each project uses its own schema for isolation.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.schema import CreateSchema

from app.config import Config


# Create base class for models
Base = declarative_base()


class VideoJob(Base):
    """
    Main table for video generation jobs.
    
    Tracks the overall status of a video generation request from start to finish.
    """
    __tablename__ = 'video_jobs'
    __table_args__ = {'schema': Config.DATABASE_SCHEMA}
    
    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(Integer, nullable=False, index=True)
    chat_id = Column(Integer, nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default='pending', index=True)
    
    # Script sections
    script = Column(Text)
    script_intro = Column(Text)
    script_main = Column(Text)
    script_outro = Column(Text)
    
    # Audio paths
    audio_intro_path = Column(String(500))
    audio_main_path = Column(String(500))
    audio_outro_path = Column(String(500))
    
    # Final video
    final_video_path = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    
    # Relationships
    segments = relationship("VideoSegment", back_populates="job", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<VideoJob(id={self.id}, status={self.status}, user_id={self.user_id})>"


class VideoSegment(Base):
    """
    Individual video segments (48 total per job).
    
    Each segment is 5 seconds long:
    - Intro: segments 0-11 (1 minute)
    - Main: segments 12-35 (2 minutes)
    - Outro: segments 36-47 (1 minute)
    """
    __tablename__ = 'video_segments'
    __table_args__ = (
        UniqueConstraint('job_id', 'segment_index', name='uq_job_segment'),
        {'schema': Config.DATABASE_SCHEMA}
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey(f'{Config.DATABASE_SCHEMA}.video_jobs.id'), nullable=False, index=True)
    segment_index = Column(Integer, nullable=False)  # 0-47
    section = Column(String(20), nullable=False)  # intro, main, outro
    
    # Text and prompts
    text_prompt = Column(Text)
    image_prompt = Column(Text)
    animation_prompt = Column(Text)  # Prompt for video animation
    
    # Generated content paths
    image_path = Column(String(500))
    video_path = Column(String(500))
    
    # Status tracking
    image_status = Column(String(20), default='pending')  # pending, generating, completed, failed
    video_status = Column(String(20), default='pending')  # pending, generating, completed, failed
    
    # Duration
    duration = Column(Float, default=5.0, nullable=False)  # 5 seconds per segment
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    job = relationship("VideoJob", back_populates="segments")
    
    def __repr__(self):
        return f"<VideoSegment(id={self.id}, job_id={self.job_id}, index={self.segment_index}, section={self.section})>"


class Approval(Base):
    """
    User approvals for different stages of video generation.
    
    Tracks when user approves script, images, or videos.
    """
    __tablename__ = 'approvals'
    __table_args__ = {'schema': Config.DATABASE_SCHEMA}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey(f'{Config.DATABASE_SCHEMA}.video_jobs.id'), nullable=False, index=True)
    approval_type = Column(String(20), nullable=False)  # script, images, videos
    status = Column(String(20), nullable=False, default='pending')  # pending, approved, rejected
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    approved_at = Column(DateTime)
    
    # Relationships
    job = relationship("VideoJob", back_populates="approvals")
    
    def __repr__(self):
        return f"<Approval(id={self.id}, job_id={self.job_id}, type={self.approval_type}, status={self.status})>"


# Database engine and session
engine = None
SessionLocal = None


def init_database():
    """
    Initialize database connection and create tables.
    
    Creates schema if it doesn't exist and all tables.
    """
    global engine, SessionLocal
    
    if not Config.DATABASE_URL:
        raise ValueError("DATABASE_URL not configured")
    
    # Create engine
    engine = create_engine(
        Config.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # Verify connections before using
        echo=Config.LOG_LEVEL == 'DEBUG'
    )
    
    # Create schema if it doesn't exist
    with engine.connect() as conn:
        if not conn.dialect.has_schema(conn, Config.DATABASE_SCHEMA):
            conn.execute(CreateSchema(Config.DATABASE_SCHEMA))
            conn.commit()
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine


def get_db():
    """
    Get database session.
    
    Use with context manager:
        with get_db() as db:
            # use db
    """
    if SessionLocal is None:
        init_database()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """
    Get database session (simple version).
    
    Returns:
        Session object
    """
    if SessionLocal is None:
        init_database()
    
    return SessionLocal()
