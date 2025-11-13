"""
Configuration module for AI Video Generator Bot.
Manages environment variables and application settings.
"""
import os
from pathlib import Path


class Config:
    """Application configuration class."""
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    TEMP_DIR = os.getenv("TEMP_DIR", str(BASE_DIR / "temp"))
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL")
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
    
    # Runway Configuration
    RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY")
    
    # Database Configuration (PostgreSQL - используется для Celery и approval system)
    DATABASE_URL = os.getenv("DATABASE_URL")
    DATABASE_SCHEMA = os.getenv("DATABASE_SCHEMA", "ai_video_bot")
    
    # Application Settings
    MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "5"))
    FILE_CLEANUP_HOURS = int(os.getenv("FILE_CLEANUP_HOURS", "1"))
    
    # FFmpeg Configuration
    FFMPEG_PATH = os.getenv("FFMPEG_PATH", str(BASE_DIR / "bin" / "ffmpeg" / "ffmpeg"))
    FFPROBE_PATH = os.getenv("FFPROBE_PATH", str(BASE_DIR / "bin" / "ffmpeg" / "ffprobe"))
    
    # Video Settings
    TARGET_VIDEO_DURATION = 240  # 4 minutes in seconds
    SEGMENT_DURATION = 5  # 5 seconds per segment
    MAX_VIDEO_SIZE_MB = 50  # Telegram file size limit
    NUM_SEGMENTS = TARGET_VIDEO_DURATION // SEGMENT_DURATION  # 48 segments
    
    # Processing Settings
    MAX_PARALLEL_SEGMENTS = 3  # Maximum parallel segment generation
    PROGRESS_UPDATE_INTERVAL = 10  # Send progress update every N segments
    
    # Retry Settings
    OPENAI_MAX_RETRIES = 3
    RUNWAY_MAX_RETRIES = 2
    RUNWAY_TASK_TIMEOUT = 300  # 5 minutes in seconds
    RUNWAY_POLLING_INTERVAL = 5  # 5 seconds
    
    # Approval Settings
    APPROVAL_TIMEOUT = 600  # 10 minutes in seconds
    APPROVAL_POLLING_INTERVAL = 2  # 2 seconds
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = 5
    RATE_LIMIT_PER_HOUR = 20
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls):
        """Validate required configuration variables."""
        required_vars = [
            ("TELEGRAM_BOT_TOKEN", cls.TELEGRAM_BOT_TOKEN),
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
            ("OPENAI_ASSISTANT_ID", cls.OPENAI_ASSISTANT_ID),
            ("RUNWAY_API_KEY", cls.RUNWAY_API_KEY),
        ]
        
        missing_vars = [var_name for var_name, var_value in required_vars if not var_value]
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist."""
        Path(cls.TEMP_DIR).mkdir(parents=True, exist_ok=True)
