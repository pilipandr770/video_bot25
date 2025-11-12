"""
FFmpeg utility module for video processing operations.
Handles video concatenation, audio addition, compression, and duration extraction.
"""

import os
import subprocess
import logging
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FFmpegError(Exception):
    """Exception raised for FFmpeg operation errors."""
    pass


class FFmpegUtil:
    """Utility class for FFmpeg operations."""
    
    def __init__(self, ffmpeg_path: Optional[str] = None, ffprobe_path: Optional[str] = None):
        """
        Initialize FFmpegUtil with paths to FFmpeg binaries.
        
        Args:
            ffmpeg_path: Path to ffmpeg binary. If None, uses default location.
            ffprobe_path: Path to ffprobe binary. If None, uses default location.
        """
        self.ffmpeg_path = ffmpeg_path or self._get_ffmpeg_path()
        self.ffprobe_path = ffprobe_path or self._get_ffprobe_path()
        
        # Verify binaries exist
        if not os.path.exists(self.ffmpeg_path):
            logger.warning(f"FFmpeg binary not found at {self.ffmpeg_path}")
        if not os.path.exists(self.ffprobe_path):
            logger.warning(f"FFprobe binary not found at {self.ffprobe_path}")
    
    @staticmethod
    def _get_ffmpeg_path() -> str:
        """
        Get the default path to FFmpeg binary.
        
        Returns:
            Path to ffmpeg binary
        """
        # Get the project root directory (2 levels up from this file)
        base_dir = Path(__file__).parent.parent.parent
        ffmpeg_path = base_dir / 'bin' / 'ffmpeg' / 'ffmpeg'
        
        # On Windows, add .exe extension
        if os.name == 'nt':
            ffmpeg_path = ffmpeg_path.with_suffix('.exe')
        
        return str(ffmpeg_path)
    
    @staticmethod
    def _get_ffprobe_path() -> str:
        """
        Get the default path to FFprobe binary.
        
        Returns:
            Path to ffprobe binary
        """
        # Get the project root directory (2 levels up from this file)
        base_dir = Path(__file__).parent.parent.parent
        ffprobe_path = base_dir / 'bin' / 'ffmpeg' / 'ffprobe'
        
        # On Windows, add .exe extension
        if os.name == 'nt':
            ffprobe_path = ffprobe_path.with_suffix('.exe')
        
        return str(ffprobe_path)
    
    def _run_command(self, command: List[str]) -> subprocess.CompletedProcess:
        """
        Run a command and return the result.
        
        Args:
            command: Command to run as list of strings
            
        Returns:
            CompletedProcess object
            
        Raises:
            FFmpegError: If command fails
        """
        logger.info(f"Running command: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Command completed successfully")
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e.stderr}")
            raise FFmpegError(f"FFmpeg command failed: {e.stderr}") from e
        except FileNotFoundError as e:
            logger.error(f"FFmpeg binary not found: {command[0]}")
            raise FFmpegError(f"FFmpeg binary not found: {command[0]}") from e
    
    def concatenate_videos(self, video_paths: List[str], output_path: str) -> str:
        """
        Concatenate multiple video files into a single video.
        
        Args:
            video_paths: List of paths to video files to concatenate
            output_path: Path where the concatenated video will be saved
            
        Returns:
            Path to the output video file
            
        Raises:
            FFmpegError: If video_paths is empty or FFmpeg command fails
        """
        if not video_paths:
            raise FFmpegError("video_paths cannot be empty")
        
        logger.info(f"Concatenating {len(video_paths)} videos to {output_path}")
        
        # Create a temporary file list for FFmpeg concat demuxer
        filelist_path = output_path + '.filelist.txt'
        
        try:
            # Write file list in FFmpeg concat format
            with open(filelist_path, 'w', encoding='utf-8') as f:
                for video_path in video_paths:
                    # Escape single quotes and use absolute paths
                    abs_path = os.path.abspath(video_path)
                    # FFmpeg concat requires specific format
                    f.write(f"file '{abs_path}'\n")
            
            # Run FFmpeg concat command
            command = [
                self.ffmpeg_path,
                '-f', 'concat',
                '-safe', '0',
                '-i', filelist_path,
                '-c', 'copy',
                '-y',  # Overwrite output file if exists
                output_path
            ]
            
            self._run_command(command)
            
            logger.info(f"Successfully concatenated videos to {output_path}")
            return output_path
            
        finally:
            # Clean up temporary file list
            if os.path.exists(filelist_path):
                os.remove(filelist_path)
    
    def add_audio(self, video_path: str, audio_path: str, output_path: str) -> str:
        """
        Add an audio track to a video file.
        
        Args:
            video_path: Path to the input video file
            audio_path: Path to the audio file to add
            output_path: Path where the output video will be saved
            
        Returns:
            Path to the output video file
            
        Raises:
            FFmpegError: If FFmpeg command fails
        """
        logger.info(f"Adding audio {audio_path} to video {video_path}")
        
        command = [
            self.ffmpeg_path,
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',  # Copy video stream without re-encoding
            '-c:a', 'aac',   # Encode audio as AAC
            '-b:a', '128k',  # Audio bitrate
            '-map', '0:v:0', # Map video from first input
            '-map', '1:a:0', # Map audio from second input
            '-shortest',     # Finish encoding when shortest stream ends
            '-y',            # Overwrite output file if exists
            output_path
        ]
        
        self._run_command(command)
        
        logger.info(f"Successfully added audio to {output_path}")
        return output_path
    
    def compress_video(self, input_path: str, output_path: str, max_size_mb: int = 50) -> str:
        """
        Compress a video file to meet a maximum size requirement.
        
        Args:
            input_path: Path to the input video file
            output_path: Path where the compressed video will be saved
            max_size_mb: Maximum size in megabytes (default: 50 for Telegram)
            
        Returns:
            Path to the output video file
            
        Raises:
            FFmpegError: If FFmpeg command fails or video duration is invalid
        """
        logger.info(f"Compressing video {input_path} to max {max_size_mb}MB")
        
        # Get video duration to calculate target bitrate
        duration = self.get_video_duration(input_path)
        
        if duration <= 0:
            raise FFmpegError(f"Invalid video duration: {duration}")
        
        # Calculate target bitrate (in kbps)
        # Formula: (target_size_mb * 8192) / duration_seconds
        # Subtract audio bitrate (128 kbps) to get video bitrate
        target_bitrate = int((max_size_mb * 8192) / duration) - 128
        
        # Ensure minimum bitrate
        target_bitrate = max(target_bitrate, 500)
        
        logger.info(f"Target video bitrate: {target_bitrate}k for {duration}s video")
        
        command = [
            self.ffmpeg_path,
            '-i', input_path,
            '-c:v', 'libx264',           # H.264 codec
            '-b:v', f'{target_bitrate}k', # Video bitrate
            '-preset', 'fast',            # Encoding speed preset
            '-crf', '28',                 # Constant Rate Factor (quality)
            '-c:a', 'aac',                # Audio codec
            '-b:a', '128k',               # Audio bitrate
            '-movflags', '+faststart',    # Enable streaming
            '-y',                         # Overwrite output file if exists
            output_path
        ]
        
        self._run_command(command)
        
        # Check output file size
        output_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"Compressed video to {output_size_mb:.2f}MB at {output_path}")
        
        return output_path
    
    def get_video_duration(self, video_path: str) -> float:
        """
        Get the duration of a video file in seconds.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Duration in seconds as a float
            
        Raises:
            FFmpegError: If FFprobe command fails or duration cannot be extracted
        """
        logger.info(f"Getting duration of video {video_path}")
        
        command = [
            self.ffprobe_path,
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        
        result = self._run_command(command)
        
        try:
            duration = float(result.stdout.strip())
            logger.info(f"Video duration: {duration}s")
            return duration
        except ValueError as e:
            logger.error(f"Failed to parse duration: {result.stdout}")
            raise FFmpegError(f"Could not extract duration from video: {e}") from e
