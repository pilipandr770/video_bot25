"""
File Manager module for managing temporary files.
Handles creation, storage, and cleanup of job-related files.
"""
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from app.config import Config


logger = logging.getLogger(__name__)


class FileManager:
    """
    Manages temporary files for video generation jobs.
    
    Handles:
    - Creating job-specific directories
    - Saving files with proper organization
    - Cleaning up job files after completion
    - Automatic cleanup of old files
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize FileManager with temporary directory.
        
        Args:
            temp_dir: Path to temporary directory. Defaults to Config.TEMP_DIR
        """
        self.temp_dir = Path(temp_dir or Config.TEMP_DIR)
        self._ensure_temp_directory()
        logger.info(f"FileManager initialized with temp_dir: {self.temp_dir}")
    
    def _ensure_temp_directory(self) -> None:
        """Ensure the temporary directory exists."""
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def create_job_directory(self, job_id: str) -> str:
        """
        Create a directory for a specific job.
        
        Creates a structured directory for storing all files related to a job:
        - {temp_dir}/{job_id}/
        - {temp_dir}/{job_id}/images/
        - {temp_dir}/{job_id}/videos/
        - {temp_dir}/{job_id}/audio/
        
        Args:
            job_id: Unique identifier for the job
            
        Returns:
            str: Path to the created job directory
            
        Raises:
            OSError: If directory creation fails
        """
        job_dir = self.temp_dir / job_id
        
        try:
            # Create main job directory
            job_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories for organized storage
            (job_dir / "images").mkdir(exist_ok=True)
            (job_dir / "videos").mkdir(exist_ok=True)
            (job_dir / "audio").mkdir(exist_ok=True)
            
            logger.info(f"Created job directory: {job_dir}")
            return str(job_dir)
            
        except OSError as e:
            logger.error(f"Failed to create job directory {job_id}: {e}")
            raise

    def save_file(self, job_id: str, filename: str, content: bytes) -> str:
        """
        Save a file to the job directory.
        
        Automatically determines the appropriate subdirectory based on file extension:
        - Images (.png, .jpg, .jpeg) -> images/
        - Videos (.mp4, .avi, .mov) -> videos/
        - Audio (.mp3, .wav, .aac) -> audio/
        - Other files -> root job directory
        
        Args:
            job_id: Unique identifier for the job
            filename: Name of the file to save
            content: Binary content of the file
            
        Returns:
            str: Full path to the saved file
            
        Raises:
            FileNotFoundError: If job directory doesn't exist
            OSError: If file write fails
        """
        job_dir = self.temp_dir / job_id
        
        if not job_dir.exists():
            raise FileNotFoundError(f"Job directory not found: {job_id}")
        
        # Determine subdirectory based on file extension
        file_ext = Path(filename).suffix.lower()
        
        if file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
            subdir = job_dir / "images"
        elif file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            subdir = job_dir / "videos"
        elif file_ext in ['.mp3', '.wav', '.aac', '.ogg', '.m4a']:
            subdir = job_dir / "audio"
        else:
            subdir = job_dir
        
        file_path = subdir / filename
        
        try:
            with open(file_path, 'wb') as f:
                f.write(content)
            
            logger.debug(f"Saved file: {file_path} ({len(content)} bytes)")
            return str(file_path)
            
        except OSError as e:
            logger.error(f"Failed to save file {filename} for job {job_id}: {e}")
            raise
    
    def cleanup_job(self, job_id: str) -> None:
        """
        Delete all files associated with a job.
        
        Removes the entire job directory and all its contents.
        Safe to call even if the directory doesn't exist.
        
        Args:
            job_id: Unique identifier for the job
        """
        job_dir = self.temp_dir / job_id
        
        if not job_dir.exists():
            logger.debug(f"Job directory already cleaned up: {job_id}")
            return
        
        try:
            shutil.rmtree(job_dir)
            logger.info(f"Cleaned up job directory: {job_id}")
            
        except OSError as e:
            logger.error(f"Failed to cleanup job directory {job_id}: {e}")
            # Don't raise - cleanup is best effort
    
    def cleanup_old_files(self, max_age_hours: Optional[int] = None) -> int:
        """
        Delete files older than the specified age.
        
        Scans the temporary directory and removes job directories
        that were created more than max_age_hours ago.
        
        Args:
            max_age_hours: Maximum age in hours. Defaults to Config.FILE_CLEANUP_HOURS
            
        Returns:
            int: Number of job directories cleaned up
        """
        max_age_hours = max_age_hours or Config.FILE_CLEANUP_HOURS
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        if not self.temp_dir.exists():
            logger.debug("Temp directory doesn't exist, nothing to clean")
            return 0
        
        try:
            for job_dir in self.temp_dir.iterdir():
                if not job_dir.is_dir():
                    continue
                
                # Get directory modification time (more reliable across platforms)
                dir_mtime = datetime.fromtimestamp(job_dir.stat().st_mtime)
                
                if dir_mtime < cutoff_time:
                    try:
                        shutil.rmtree(job_dir)
                        cleaned_count += 1
                        logger.info(
                            f"Cleaned up old job directory: {job_dir.name} "
                            f"(modified: {dir_mtime})"
                        )
                    except OSError as e:
                        logger.error(f"Failed to cleanup old directory {job_dir.name}: {e}")
            
            logger.info(
                f"Cleanup completed: removed {cleaned_count} job directories "
                f"older than {max_age_hours} hours"
            )
            return cleaned_count
            
        except OSError as e:
            logger.error(f"Error during cleanup_old_files: {e}")
            return cleaned_count
    
    def get_job_directory(self, job_id: str) -> Optional[str]:
        """
        Get the path to a job directory if it exists.
        
        Args:
            job_id: Unique identifier for the job
            
        Returns:
            str: Path to job directory, or None if it doesn't exist
        """
        job_dir = self.temp_dir / job_id
        return str(job_dir) if job_dir.exists() else None
    
    def get_job_files(self, job_id: str, subdir: Optional[str] = None) -> list[str]:
        """
        Get list of files in a job directory.
        
        Args:
            job_id: Unique identifier for the job
            subdir: Optional subdirectory (images, videos, audio)
            
        Returns:
            list[str]: List of file paths
        """
        job_dir = self.temp_dir / job_id
        
        if not job_dir.exists():
            return []
        
        target_dir = job_dir / subdir if subdir else job_dir
        
        if not target_dir.exists():
            return []
        
        try:
            return [str(f) for f in target_dir.iterdir() if f.is_file()]
        except OSError as e:
            logger.error(f"Error listing files for job {job_id}: {e}")
            return []
    
    def get_disk_usage(self) -> dict:
        """
        Get disk usage statistics for the temporary directory.
        
        Returns:
            dict: Dictionary with total_size_mb and job_count
        """
        if not self.temp_dir.exists():
            return {"total_size_mb": 0, "job_count": 0}
        
        total_size = 0
        job_count = 0
        
        try:
            for job_dir in self.temp_dir.iterdir():
                if job_dir.is_dir():
                    job_count += 1
                    for file_path in job_dir.rglob('*'):
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
            
            return {
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "job_count": job_count
            }
            
        except OSError as e:
            logger.error(f"Error calculating disk usage: {e}")
            return {"total_size_mb": 0, "job_count": 0}
