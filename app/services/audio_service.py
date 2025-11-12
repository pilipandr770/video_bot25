"""
Audio Service for AI Video Generator Bot.
Handles audio generation and duration adjustment for video voiceovers.
"""
import os
import logging
import subprocess
from typing import Optional
from pathlib import Path

from app.services.openai_service import OpenAIService, OpenAIServiceError
from app.utils.ffmpeg import FFmpegUtil
from app.config import Config


logger = logging.getLogger(__name__)


class AudioServiceError(Exception):
    """Base exception for Audio service errors."""
    pass


class AudioService:
    """Service for generating and processing audio for videos."""
    
    def __init__(
        self,
        openai_service: Optional[OpenAIService] = None,
        ffmpeg_util: Optional[FFmpegUtil] = None
    ):
        """
        Initialize Audio service.
        
        Args:
            openai_service: OpenAI service instance (creates new if None)
            ffmpeg_util: FFmpeg utility instance (creates new if None)
        """
        self.openai_service = openai_service or OpenAIService()
        self.ffmpeg_util = ffmpeg_util or FFmpegUtil()
        
        logger.info("Audio service initialized")
    
    def generate_audio(
        self,
        script: str,
        output_path: str,
        target_duration: int = Config.TARGET_VIDEO_DURATION,
        voice: str = "alloy"
    ) -> str:
        """
        Generate audio file from script text with target duration.
        
        This method generates speech from the script using OpenAI TTS,
        then adjusts the audio duration to match the target video duration.
        
        Args:
            script: Full script text to convert to speech
            output_path: Path where the audio file will be saved
            target_duration: Target duration in seconds (default: 240s/4min)
            voice: Voice to use for TTS (default: "alloy")
            
        Returns:
            Path to the generated audio file
            
        Raises:
            AudioServiceError: If audio generation fails
            OpenAIServiceError: If TTS API call fails
        """
        logger.info("Starting audio generation", extra={
            "script_length": len(script),
            "target_duration": target_duration,
            "voice": voice,
            "output_path": output_path
        })
        
        try:
            # Generate speech using OpenAI TTS
            logger.info("Generating speech from script")
            audio_content = self.openai_service.generate_speech(
                text=script,
                voice=voice,
                model="tts-1"  # Use standard model for faster generation
            )
            
            # Save the raw audio to a temporary file
            temp_audio_path = output_path + ".temp.mp3"
            
            logger.info(f"Saving raw audio to {temp_audio_path}")
            with open(temp_audio_path, 'wb') as f:
                f.write(audio_content)
            
            # Get the actual duration of generated audio
            actual_duration = self._get_audio_duration(temp_audio_path)
            
            logger.info(f"Generated audio duration: {actual_duration}s, target: {target_duration}s")
            
            # Adjust duration if needed
            if abs(actual_duration - target_duration) > 1.0:  # More than 1 second difference
                logger.info("Adjusting audio duration to match target")
                self.adjust_audio_duration(
                    audio_path=temp_audio_path,
                    target_duration=target_duration,
                    output_path=output_path
                )
                
                # Clean up temporary file
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
            else:
                # Duration is close enough, just rename the file
                logger.info("Audio duration is within acceptable range, no adjustment needed")
                os.rename(temp_audio_path, output_path)
            
            # Verify final audio file exists
            if not os.path.exists(output_path):
                raise AudioServiceError(f"Audio file was not created at {output_path}")
            
            final_duration = self._get_audio_duration(output_path)
            audio_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            
            logger.info("Audio generation completed", extra={
                "output_path": output_path,
                "final_duration": final_duration,
                "audio_size_mb": audio_size_mb
            })
            
            return output_path
            
        except OpenAIServiceError as e:
            logger.error(f"OpenAI TTS failed: {e}")
            raise AudioServiceError(f"Failed to generate speech: {e}") from e
            
        except Exception as e:
            logger.error(f"Unexpected error during audio generation: {e}")
            # Clean up temporary file if it exists
            temp_audio_path = output_path + ".temp.mp3"
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            raise AudioServiceError(f"Audio generation failed: {e}") from e
    
    def adjust_audio_duration(
        self,
        audio_path: str,
        target_duration: int,
        output_path: str
    ) -> str:
        """
        Adjust audio duration to match target duration using FFmpeg.
        
        This method uses FFmpeg's atempo filter to speed up or slow down
        the audio to match the target duration. The atempo filter preserves
        pitch while changing speed.
        
        Args:
            audio_path: Path to the input audio file
            target_duration: Target duration in seconds
            output_path: Path where the adjusted audio will be saved
            
        Returns:
            Path to the adjusted audio file
            
        Raises:
            AudioServiceError: If duration adjustment fails
        """
        logger.info("Adjusting audio duration", extra={
            "audio_path": audio_path,
            "target_duration": target_duration,
            "output_path": output_path
        })
        
        try:
            # Get current duration
            current_duration = self._get_audio_duration(audio_path)
            
            if current_duration <= 0:
                raise AudioServiceError(f"Invalid audio duration: {current_duration}")
            
            # Calculate speed factor
            # If audio is too long, speed it up (factor > 1)
            # If audio is too short, slow it down (factor < 1)
            speed_factor = current_duration / target_duration
            
            logger.info(f"Adjusting audio speed by factor: {speed_factor:.3f}")
            
            # FFmpeg atempo filter has limits: 0.5 to 2.0
            # If we need more adjustment, chain multiple atempo filters
            atempo_filters = []
            remaining_factor = speed_factor
            
            while remaining_factor > 2.0:
                atempo_filters.append("atempo=2.0")
                remaining_factor /= 2.0
            
            while remaining_factor < 0.5:
                atempo_filters.append("atempo=0.5")
                remaining_factor /= 0.5
            
            # Add the final adjustment
            if remaining_factor != 1.0:
                atempo_filters.append(f"atempo={remaining_factor:.6f}")
            
            # Build FFmpeg command
            filter_chain = ",".join(atempo_filters) if atempo_filters else "anull"
            
            command = [
                self.ffmpeg_util.ffmpeg_path,
                '-i', audio_path,
                '-filter:a', filter_chain,
                '-c:a', 'aac',      # Encode as AAC
                '-b:a', '128k',     # Audio bitrate
                '-y',               # Overwrite output file if exists
                output_path
            ]
            
            logger.info(f"Running FFmpeg command: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Verify output
            if not os.path.exists(output_path):
                raise AudioServiceError(f"Adjusted audio file was not created at {output_path}")
            
            adjusted_duration = self._get_audio_duration(output_path)
            
            logger.info("Audio duration adjusted successfully", extra={
                "original_duration": current_duration,
                "adjusted_duration": adjusted_duration,
                "target_duration": target_duration,
                "speed_factor": speed_factor
            })
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg command failed: {e.stderr}")
            raise AudioServiceError(f"Failed to adjust audio duration: {e.stderr}") from e
            
        except Exception as e:
            logger.error(f"Unexpected error during audio adjustment: {e}")
            raise AudioServiceError(f"Audio duration adjustment failed: {e}") from e
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """
        Get the duration of an audio file in seconds.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Duration in seconds as a float
            
        Raises:
            AudioServiceError: If duration cannot be extracted
        """
        try:
            command = [
                self.ffmpeg_util.ffprobe_path,
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                audio_path
            ]
            
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True
            )
            
            duration = float(result.stdout.strip())
            return duration
            
        except (subprocess.CalledProcessError, ValueError) as e:
            logger.error(f"Failed to get audio duration: {e}")
            raise AudioServiceError(f"Could not extract audio duration: {e}") from e
