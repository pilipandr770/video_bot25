"""
Data models for video generation jobs.

This module defines the core data structures used throughout the video generation pipeline,
including job tracking, script segments, and video segments.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List


class JobStatus(Enum):
    """Status states for video generation jobs."""
    PENDING = "pending"
    GENERATING_SCRIPT = "generating_script"
    AWAITING_SCRIPT_APPROVAL = "awaiting_script_approval"
    SCRIPT_APPROVED = "script_approved"
    GENERATING_IMAGES = "generating_images"
    AWAITING_IMAGES_APPROVAL = "awaiting_images_approval"
    IMAGES_APPROVED = "images_approved"
    ANIMATING_VIDEOS = "animating_videos"
    AWAITING_VIDEOS_APPROVAL = "awaiting_videos_approval"
    VIDEOS_APPROVED = "videos_approved"
    GENERATING_AUDIO = "generating_audio"
    ASSEMBLING_VIDEO = "assembling_video"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class SegmentStatus(Enum):
    """Status states for individual video segments."""
    PENDING = "pending"
    GENERATING_IMAGE = "generating_image"
    IMAGE_READY = "image_ready"
    ANIMATING = "animating"
    VIDEO_READY = "video_ready"
    FAILED = "failed"


@dataclass
class ScriptSegment:
    """
    Represents a 5-second segment of the video script.
    
    Each segment contains the text content, timing information,
    and prompts for image generation and animation.
    """
    index: int
    text: str
    start_time: float
    end_time: float
    image_prompt: str
    animation_prompt: str


@dataclass
class VideoSegment:
    """
    Represents a generated video segment with associated assets.
    
    Tracks the generation status and file paths for both the image
    and animated video, along with Runway API task IDs.
    """
    index: int
    script_segment: ScriptSegment
    image_path: Optional[str] = None
    video_path: Optional[str] = None
    runway_image_task_id: Optional[str] = None
    runway_video_task_id: Optional[str] = None
    status: SegmentStatus = SegmentStatus.PENDING


@dataclass
class VideoJob:
    """
    Main job tracking model for video generation requests.
    
    Contains all information about a video generation job including
    user details, processing status, script segments, generated assets,
    and error information.
    """
    job_id: str
    user_id: int
    chat_id: int
    prompt: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    script: Optional[str] = None
    segments: List[ScriptSegment] = field(default_factory=list)
    video_segments: List[VideoSegment] = field(default_factory=list)
    audio_path: Optional[str] = None
    final_video_path: Optional[str] = None
    error_message: Optional[str] = None
