"""
Enhanced Video Job Model with detailed segment tracking.
Stores all intermediate data for each generation step.
"""

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.database import Base


class VideoJobEnhanced(Base):
    """Enhanced video job with detailed tracking."""
    
    __tablename__ = 'video_jobs_enhanced'
    __table_args__ = {'schema': 'ai_video_bot'}
    
    # Primary fields
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    chat_id = Column(Integer, nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default='pending')
    
    # Script stage
    script_text = Column(Text, nullable=True)
    script_approved = Column(Integer, default=0)  # 0=pending, 1=approved, -1=rejected
    script_generated_at = Column(DateTime, nullable=True)
    
    # Audio stage
    audio_path = Column(String(500), nullable=True)
    audio_duration = Column(Float, nullable=True)
    audio_generated_at = Column(DateTime, nullable=True)
    
    # Final video
    final_video_path = Column(String(500), nullable=True)
    final_video_size_mb = Column(Float, nullable=True)
    final_video_duration = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    segments = relationship("VideoSegmentEnhanced", back_populates="job", cascade="all, delete-orphan")


class VideoSegmentEnhanced(Base):
    """Individual video segment with all generation stages."""
    
    __tablename__ = 'video_segments_enhanced'
    __table_args__ = {'schema': 'ai_video_bot'}
    
    # Primary fields
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey('ai_video_bot.video_jobs_enhanced.id'), nullable=False)
    segment_index = Column(Integer, nullable=False)  # 0-9 for 10 segments
    
    # Script segment
    text = Column(Text, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    
    # Image prompt generation (via Segment Assistant)
    image_prompt = Column(Text, nullable=True)
    image_prompt_generated_at = Column(DateTime, nullable=True)
    
    # Image generation (via Runway)
    image_path = Column(String(500), nullable=True)
    image_runway_task_id = Column(String(100), nullable=True)
    image_generated_at = Column(DateTime, nullable=True)
    
    # Animation prompt generation (via Animation Assistant)
    animation_prompt = Column(Text, nullable=True)
    animation_prompt_generated_at = Column(DateTime, nullable=True)
    
    # Video generation (via Runway)
    video_path = Column(String(500), nullable=True)
    video_runway_task_id = Column(String(100), nullable=True)
    video_duration = Column(Float, nullable=True)
    video_generated_at = Column(DateTime, nullable=True)
    
    # Status tracking
    status = Column(String(50), default='pending')  # pending, image_prompt_ready, image_ready, animation_prompt_ready, video_ready
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    job = relationship("VideoJobEnhanced", back_populates="segments")
    
    def __repr__(self):
        return f"<VideoSegmentEnhanced(job_id={self.job_id}, index={self.segment_index}, status={self.status})>"
