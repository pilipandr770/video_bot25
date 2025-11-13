"""
Video Generation Task for AI Video Generator Bot.

Main Celery task that orchestrates the complete video generation pipeline
with user approval stages for script, images, and videos.
"""

import logging
import structlog
import os
import time
import asyncio
from typing import Optional
from telegram import Bot
from telegram.error import TelegramError

from app.tasks import celery_app
from app.config import Config
from app.models.video_job import VideoJob, JobStatus
from app.services.openai_service import OpenAIService, OpenAIServiceError
from app.services.runway_service import RunwayService
from app.services.script_service import ScriptService
from app.services.video_service import VideoService
from app.services.audio_service import AudioService
from app.services.approval_service import ApprovalManager
from app.bot.notifications import NotificationService
from app.utils.file_manager import FileManager
from app.utils.ffmpeg import FFmpegUtil


logger = structlog.get_logger(__name__)


class VideoGenerationError(Exception):
    """Base exception for video generation errors."""
    pass


@celery_app.task(bind=True, max_retries=3, name='app.tasks.generate_video')
def generate_video_task(
    self,
    job_id: str,
    user_id: int,
    chat_id: int,
    prompt: str
) -> dict:
    """
    Main Celery task for generating video with approval stages.
    
    Pipeline stages:
    1. Generate script via OpenAI Assistant
    2. ⏸️ Wait for script approval
    3. Generate images via Runway API
    4. ⏸️ Wait for images approval (preview first 5)
    5. Animate images via Runway API
    6. ⏸️ Wait for videos approval (preview first 3)
    7. Generate audio via OpenAI TTS
    8. Assemble final video via FFmpeg
    9. Send final video to user
    10. Cleanup temporary files
    
    Args:
        job_id: Unique identifier for the job
        user_id: Telegram user ID
        chat_id: Telegram chat ID
        prompt: User's video description
        
    Returns:
        dict: Job result with status and paths
        
    Raises:
        VideoGenerationError: If generation fails after retries
    """
    # Start timing the entire job
    job_start_time = time.time()
    
    logger.info(
        "video_generation_started",
        job_id=job_id,
        user_id=user_id,
        chat_id=chat_id,
        prompt_length=len(prompt),
        prompt_preview=prompt[:100]
    )
    
    # Initialize services
    file_manager = FileManager()
    openai_service = OpenAIService()
    runway_service = RunwayService(Config.RUNWAY_API_KEY)
    script_service = ScriptService()
    video_service = VideoService(runway_service, script_service, file_manager)
    audio_service = AudioService(openai_service)
    ffmpeg_util = FFmpegUtil()
    notification_service = NotificationService()
    
    # Initialize approval manager with PostgreSQL
    approval_manager = ApprovalManager()
    
    # Create job directory
    job_dir = file_manager.create_job_directory(job_id)
    
    # Create VideoJob record in database
    from app.models.database import VideoJob as VideoJobDB, get_db_session
    db = get_db_session()
    try:
        video_job = VideoJobDB(
            id=job_id,
            user_id=user_id,
            chat_id=chat_id,
            prompt=prompt,
            status='processing'
        )
        db.add(video_job)
        db.commit()
        logger.info("video_job_created_in_db", job_id=job_id)
    except Exception as e:
        logger.error("failed_to_create_video_job", job_id=job_id, error=str(e), exc_info=True)
        db.rollback()
        raise VideoGenerationError(f"Failed to create job in database: {str(e)}") from e
    finally:
        db.close()
    
    # Track metrics for each stage
    metrics = {
        "job_id": job_id,
        "stages": {}
    }
    
    try:
        # ========== STAGE 0: Handle Voice Message (if applicable) ==========
        actual_prompt = prompt
        
        # Check if this is a voice message that needs transcription
        if prompt.startswith("__VOICE_MESSAGE__|"):
            stage_start = time.time()
            logger.info("stage_started", job_id=job_id, stage="transcribe_voice", stage_number=0)
            asyncio.run(notification_service.send_status_update(
                chat_id, 
                JobStatus.GENERATING_SCRIPT,  # Use existing status
                job_id,
                custom_message="🎤 Распознаю голосовое сообщение..."
            ))
            
            try:
                actual_prompt = _transcribe_voice_message(
                    prompt,
                    openai_service,
                    job_id,
                    chat_id
                )
                
                stage_duration = time.time() - stage_start
                logger.info(
                    "stage_completed",
                    job_id=job_id,
                    stage="transcribe_voice",
                    duration_seconds=round(stage_duration, 2),
                    transcribed_length=len(actual_prompt),
                    transcribed_words=len(actual_prompt.split())
                )
                
                # Send transcribed text to user for confirmation
                asyncio.run(notification_service.send_message(
                    chat_id,
                    f"✅ Голосовое сообщение распознано:\n\n\"{actual_prompt}\"\n\n"
                    f"Начинаю генерацию сценария..."
                ))
                
            except Exception as e:
                logger.error(
                    "voice_transcription_failed",
                    job_id=job_id,
                    error=str(e),
                    exc_info=True
                )
                asyncio.run(notification_service.send_error_message(
                    chat_id,
                    "transcription_error",
                    job_id
                ))
                raise VideoGenerationError(f"Failed to transcribe voice message: {str(e)}") from e
        
        # ========== STAGE 1: Generate Script ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="generate_script", stage_number=1)
        asyncio.run(notification_service.send_status_update(chat_id, JobStatus.GENERATING_SCRIPT, job_id))
        
        script = _generate_script(openai_service, actual_prompt, job_id)
        
        stage_duration = time.time() - stage_start
        metrics["stages"]["generate_script"] = {
            "duration_seconds": round(stage_duration, 2),
            "script_length": len(script),
            "script_words": len(script.split())
        }
        
        logger.info(
            "stage_completed",
            job_id=job_id,
            stage="generate_script",
            duration_seconds=round(stage_duration, 2),
            script_length=len(script),
            script_words=len(script.split())
        )
        
        # ========== STAGE 2: Script Approval ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="script_approval", stage_number=2)
        asyncio.run(notification_service.send_status_update(chat_id, JobStatus.AWAITING_SCRIPT_APPROVAL, job_id))
        asyncio.run(notification_service.send_script_approval(chat_id, job_id, script))
        
        approved = approval_manager.wait_for_approval(
            job_id,
            'script',
            timeout=Config.APPROVAL_TIMEOUT
        )
        
        stage_duration = time.time() - stage_start
        
        if not approved:
            logger.info(
                "job_cancelled",
                job_id=job_id,
                stage="script_approval",
                reason="user_cancelled_or_timeout",
                wait_duration_seconds=round(stage_duration, 2)
            )
            _handle_cancellation(job_id, file_manager, notification_service, chat_id, "script")
            return {"status": "cancelled", "stage": "script_approval"}
        
        metrics["stages"]["script_approval"] = {
            "duration_seconds": round(stage_duration, 2),
            "approved": True
        }
        
        logger.info(
            "stage_completed",
            job_id=job_id,
            stage="script_approval",
            duration_seconds=round(stage_duration, 2),
            approved=True
        )
        asyncio.run(notification_service.send_status_update(chat_id, JobStatus.SCRIPT_APPROVED, job_id))
        
        # ========== STAGE 3: Generate Images ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="generate_images", stage_number=3)
        asyncio.run(notification_service.send_status_update(chat_id, JobStatus.GENERATING_IMAGES, job_id))
        
        segments = script_service.split_script(script)
        logger.info(
            "script_segmented",
            job_id=job_id,
            segment_count=len(segments),
            target_duration=Config.TARGET_VIDEO_DURATION
        )
        
        # Generate images for all segments
        video_segments = _generate_images(
            video_service,
            job_id,
            segments,
            notification_service,
            chat_id
        )
        
        stage_duration = time.time() - stage_start
        successful_images = len([s for s in video_segments if s.image_path])
        metrics["stages"]["generate_images"] = {
            "duration_seconds": round(stage_duration, 2),
            "total_segments": len(segments),
            "successful_images": successful_images,
            "avg_time_per_image": round(stage_duration / len(segments), 2) if segments else 0
        }
        
        logger.info(
            "stage_completed",
            job_id=job_id,
            stage="generate_images",
            duration_seconds=round(stage_duration, 2),
            total_segments=len(segments),
            successful_images=successful_images
        )
        
        # ========== STAGE 4: Images Approval ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="images_approval", stage_number=4)
        asyncio.run(notification_service.send_status_update(chat_id, JobStatus.AWAITING_IMAGES_APPROVAL, job_id))
        
        # Get first 5 image paths for preview
        preview_images = [
            seg.image_path for seg in video_segments[:5]
            if seg.image_path
        ]
        asyncio.run(notification_service.send_images_approval(chat_id, job_id, preview_images))
        
        approved = approval_manager.wait_for_approval(
            job_id,
            'images',
            timeout=Config.APPROVAL_TIMEOUT
        )
        
        stage_duration = time.time() - stage_start
        
        if not approved:
            logger.info(
                "job_cancelled",
                job_id=job_id,
                stage="images_approval",
                reason="user_cancelled_or_timeout",
                wait_duration_seconds=round(stage_duration, 2)
            )
            _handle_cancellation(job_id, file_manager, notification_service, chat_id, "images")
            return {"status": "cancelled", "stage": "images_approval"}
        
        metrics["stages"]["images_approval"] = {
            "duration_seconds": round(stage_duration, 2),
            "approved": True,
            "preview_count": len(preview_images)
        }
        
        logger.info(
            "stage_completed",
            job_id=job_id,
            stage="images_approval",
            duration_seconds=round(stage_duration, 2),
            approved=True
        )
        asyncio.run(notification_service.send_status_update(chat_id, JobStatus.IMAGES_APPROVED, job_id))
        
        # ========== STAGE 5: Animate Videos ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="animate_videos", stage_number=5)
        asyncio.run(notification_service.send_status_update(chat_id, JobStatus.ANIMATING_VIDEOS, job_id))
        
        video_segments = _animate_videos(
            video_service,
            runway_service,
            job_id,
            video_segments,
            notification_service,
            chat_id
        )
        
        stage_duration = time.time() - stage_start
        successful_videos = len([s for s in video_segments if s.video_path])
        metrics["stages"]["animate_videos"] = {
            "duration_seconds": round(stage_duration, 2),
            "total_segments": len(video_segments),
            "successful_videos": successful_videos,
            "avg_time_per_video": round(stage_duration / len(video_segments), 2) if video_segments else 0
        }
        
        logger.info(
            "stage_completed",
            job_id=job_id,
            stage="animate_videos",
            duration_seconds=round(stage_duration, 2),
            successful_videos=successful_videos
        )
        
        # ========== STAGE 6: Videos Approval ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="videos_approval", stage_number=6)
        asyncio.run(notification_service.send_status_update(chat_id, JobStatus.AWAITING_VIDEOS_APPROVAL, job_id))
        
        # Get first 3 video paths for preview
        preview_videos = [
            seg.video_path for seg in video_segments[:3]
            if seg.video_path
        ]
        asyncio.run(notification_service.send_videos_approval(chat_id, job_id, preview_videos))
        
        approved = approval_manager.wait_for_approval(
            job_id,
            'videos',
            timeout=Config.APPROVAL_TIMEOUT
        )
        
        stage_duration = time.time() - stage_start
        
        if not approved:
            logger.info(
                "job_cancelled",
                job_id=job_id,
                stage="videos_approval",
                reason="user_cancelled_or_timeout",
                wait_duration_seconds=round(stage_duration, 2)
            )
            _handle_cancellation(job_id, file_manager, notification_service, chat_id, "videos")
            return {"status": "cancelled", "stage": "videos_approval"}
        
        metrics["stages"]["videos_approval"] = {
            "duration_seconds": round(stage_duration, 2),
            "approved": True,
            "preview_count": len(preview_videos)
        }
        
        logger.info(
            "stage_completed",
            job_id=job_id,
            stage="videos_approval",
            duration_seconds=round(stage_duration, 2),
            approved=True
        )
        asyncio.run(notification_service.send_status_update(chat_id, JobStatus.VIDEOS_APPROVED, job_id))
        
        # ========== STAGE 7: Generate Audio ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="generate_audio", stage_number=7)
        asyncio.run(notification_service.send_status_update(chat_id, JobStatus.GENERATING_AUDIO, job_id))
        
        audio_path = _generate_audio(
            audio_service,
            script,
            job_id,
            job_dir
        )
        
        stage_duration = time.time() - stage_start
        audio_size_mb = os.path.getsize(audio_path) / (1024 * 1024) if os.path.exists(audio_path) else 0
        metrics["stages"]["generate_audio"] = {
            "duration_seconds": round(stage_duration, 2),
            "audio_size_mb": round(audio_size_mb, 2)
        }
        
        logger.info(
            "stage_completed",
            job_id=job_id,
            stage="generate_audio",
            duration_seconds=round(stage_duration, 2),
            audio_size_mb=round(audio_size_mb, 2)
        )
        
        # ========== STAGE 8: Assemble Final Video ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="assemble_video", stage_number=8)
        asyncio.run(notification_service.send_status_update(chat_id, JobStatus.ASSEMBLING_VIDEO, job_id))
        
        final_video_path = _assemble_final_video(
            ffmpeg_util,
            video_segments,
            audio_path,
            job_id,
            job_dir
        )
        
        stage_duration = time.time() - stage_start
        video_size_mb = os.path.getsize(final_video_path) / (1024 * 1024) if os.path.exists(final_video_path) else 0
        video_duration = ffmpeg_util.get_video_duration(final_video_path) if os.path.exists(final_video_path) else 0
        
        metrics["stages"]["assemble_video"] = {
            "duration_seconds": round(stage_duration, 2),
            "video_size_mb": round(video_size_mb, 2),
            "video_duration_seconds": round(video_duration, 2)
        }
        
        logger.info(
            "stage_completed",
            job_id=job_id,
            stage="assemble_video",
            duration_seconds=round(stage_duration, 2),
            video_size_mb=round(video_size_mb, 2),
            video_duration_seconds=round(video_duration, 2)
        )
        
        # ========== STAGE 9: Send Final Video ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="send_video", stage_number=9)
        asyncio.run(notification_service.send_final_video(
            chat_id, 
            final_video_path, 
            job_id=job_id,
            duration_seconds=int(total_duration)
        ))
        asyncio.run(notification_service.send_status_update(chat_id, JobStatus.COMPLETED, job_id))
        
        stage_duration = time.time() - stage_start
        metrics["stages"]["send_video"] = {
            "duration_seconds": round(stage_duration, 2)
        }
        
        logger.info(
            "stage_completed",
            job_id=job_id,
            stage="send_video",
            duration_seconds=round(stage_duration, 2)
        )
        
        # ========== STAGE 10: Cleanup ==========
        logger.info("stage_started", job_id=job_id, stage="cleanup", stage_number=10)
        file_manager.cleanup_job(job_id)
        logger.info("stage_completed", job_id=job_id, stage="cleanup")
        
        # Calculate total job duration
        total_duration = time.time() - job_start_time
        metrics["total_duration_seconds"] = round(total_duration, 2)
        metrics["total_duration_minutes"] = round(total_duration / 60, 2)
        
        logger.info(
            "video_generation_completed",
            job_id=job_id,
            total_duration_seconds=round(total_duration, 2),
            total_duration_minutes=round(total_duration / 60, 2),
            final_video_size_mb=round(video_size_mb, 2),
            metrics=metrics
        )
        
        return {
            "status": "completed",
            "job_id": job_id,
            "final_video_path": final_video_path,
            "metrics": metrics
        }
        
    except Exception as e:
        total_duration = time.time() - job_start_time
        
        logger.error(
            "video_generation_failed",
            job_id=job_id,
            error=str(e),
            error_type=type(e).__name__,
            duration_seconds=round(total_duration, 2),
            metrics=metrics,
            exc_info=True
        )
        
        # Send error notification to user
        error_type = _map_exception_to_error_type(e)
        asyncio.run(notification_service.send_error_message(chat_id, error_type, job_id))
        
        # Cleanup on error
        try:
            file_manager.cleanup_job(job_id)
            logger.info("cleanup_completed_after_error", job_id=job_id)
        except Exception as cleanup_error:
            logger.error(
                "cleanup_failed",
                job_id=job_id,
                error=str(cleanup_error),
                exc_info=True
            )
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(
                "task_retry_scheduled",
                job_id=job_id,
                attempt=self.request.retries + 1,
                max_retries=self.max_retries,
                countdown_seconds=60
            )
            raise self.retry(exc=e, countdown=60)
        
        raise VideoGenerationError(f"Video generation failed: {str(e)}") from e


# ========== Helper Functions ==========

def _transcribe_voice_message(
    prompt: str,
    openai_service: OpenAIService,
    job_id: str,
    chat_id: int
) -> str:
    """
    Transcribe voice message from Telegram.
    
    Args:
        prompt: Special marker string in format "__VOICE_MESSAGE__|{file_id}"
        openai_service: OpenAI service instance
        job_id: Job identifier for logging
        chat_id: Telegram chat ID
        
    Returns:
        Transcribed text from the voice message
        
    Raises:
        VideoGenerationError: If transcription fails
    """
    try:
        # Extract file_id from the marker
        if not prompt.startswith("__VOICE_MESSAGE__|"):
            raise ValueError(f"Invalid voice message marker format: {prompt}")
        
        file_id = prompt.split("|", 1)[1]
        
        logger.info(
            "voice_download_started",
            job_id=job_id,
            file_id=file_id
        )
        
        # Initialize Telegram bot
        bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        
        # Download voice file from Telegram
        # We need to run this in an async context
        async def download_voice():
            voice_file = await bot.get_file(file_id)
            voice_bytes = await voice_file.download_as_bytearray()
            return bytes(voice_bytes)
        
        voice_bytes = asyncio.run(download_voice())
        
        logger.info(
            "voice_download_completed",
            job_id=job_id,
            file_id=file_id,
            size_bytes=len(voice_bytes),
            size_mb=round(len(voice_bytes) / (1024 * 1024), 2)
        )
        
        # Transcribe using OpenAI Whisper
        logger.info(
            "voice_transcription_started",
            job_id=job_id,
            file_id=file_id
        )
        
        transcribed_text = openai_service.transcribe_audio(
            audio_file=voice_bytes,
            filename="voice_message.ogg"
        )
        
        if not transcribed_text or not transcribed_text.strip():
            raise ValueError("Transcription resulted in empty text")
        
        logger.info(
            "voice_transcription_completed",
            job_id=job_id,
            file_id=file_id,
            transcribed_length=len(transcribed_text),
            transcribed_words=len(transcribed_text.split())
        )
        
        return transcribed_text.strip()
        
    except TelegramError as e:
        logger.error(
            "telegram_download_failed",
            job_id=job_id,
            error=str(e),
            exc_info=True
        )
        raise VideoGenerationError(
            f"Failed to download voice message from Telegram: {str(e)}"
        ) from e
        
    except OpenAIServiceError as e:
        logger.error(
            "openai_transcription_failed",
            job_id=job_id,
            error=str(e),
            exc_info=True
        )
        raise VideoGenerationError(
            f"Failed to transcribe voice message: {str(e)}"
        ) from e
        
    except Exception as e:
        logger.error(
            "voice_processing_failed",
            job_id=job_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise VideoGenerationError(
            f"Unexpected error processing voice message: {str(e)}"
        ) from e


def _generate_script(
    openai_service: OpenAIService,
    prompt: str,
    job_id: str
) -> str:
    """Generate script using OpenAI Assistant."""
    try:
        script = openai_service.generate_script(prompt)
        return script
    except OpenAIServiceError as e:
        logger.error(f"[{job_id}] Script generation failed: {e}")
        raise VideoGenerationError(f"Failed to generate script: {e}") from e


def _generate_images(
    video_service: VideoService,
    job_id: str,
    segments,
    notification_service: NotificationService,
    chat_id: int
):
    """Generate images for all segments with progress updates."""
    
    try:
        # Use the new generate_images_only method for Stage 3
        def progress_callback(current, total):
            asyncio.run(notification_service.send_progress_update(
                chat_id, 
                current, 
                total, 
                "генерации изображений",
                job_id
            ))
        
        video_segments = video_service.generate_images_only(
            job_id,
            segments,
            progress_callback=progress_callback
        )
        
        return video_segments
        
    except Exception as e:
        logger.error(f"[{job_id}] Image generation failed: {e}")
        raise VideoGenerationError(f"Failed to generate images: {e}") from e


def _animate_videos(
    video_service: VideoService,
    runway_service: RunwayService,
    job_id: str,
    video_segments,
    notification_service: NotificationService,
    chat_id: int
):
    """Animate all video segments with progress updates."""
    
    try:
        # Use the new animate_images_only method for Stage 5
        def progress_callback(current, total):
            asyncio.run(notification_service.send_progress_update(
                chat_id, 
                current, 
                total, 
                "анимации видео",
                job_id
            ))
        
        animated_segments = video_service.animate_images_only(
            job_id,
            video_segments,
            progress_callback=progress_callback
        )
        
        return animated_segments
        
    except Exception as e:
        logger.error(f"[{job_id}] Video animation failed: {e}")
        raise VideoGenerationError(f"Failed to animate videos: {e}") from e


def _generate_audio(
    audio_service: AudioService,
    script: str,
    job_id: str,
    job_dir: str
) -> str:
    """Generate audio from script."""
    try:
        audio_path = os.path.join(job_dir, "audio", "voiceover.mp3")
        audio_service.generate_audio(
            script=script,
            output_path=audio_path,
            target_duration=Config.TARGET_VIDEO_DURATION
        )
        return audio_path
    except Exception as e:
        logger.error(f"[{job_id}] Audio generation failed: {e}")
        raise VideoGenerationError(f"Failed to generate audio: {e}") from e


def _assemble_final_video(
    ffmpeg_util: FFmpegUtil,
    video_segments,
    audio_path: str,
    job_id: str,
    job_dir: str
) -> str:
    """Assemble final video from segments and audio."""
    try:
        # Get all video segment paths in order
        video_paths = [
            seg.video_path for seg in sorted(video_segments, key=lambda x: x.index)
            if seg.video_path
        ]
        
        if not video_paths:
            raise VideoGenerationError("No video segments available for assembly")
        
        # Concatenate videos
        concatenated_path = os.path.join(job_dir, "concatenated.mp4")
        ffmpeg_util.concatenate_videos(video_paths, concatenated_path)
        
        # Add audio
        final_path = os.path.join(job_dir, "final_video.mp4")
        ffmpeg_util.add_audio(concatenated_path, audio_path, final_path)
        
        # Check file size and compress if needed
        file_size_mb = os.path.getsize(final_path) / (1024 * 1024)
        
        if file_size_mb > Config.MAX_VIDEO_SIZE_MB:
            logger.info(
                f"[{job_id}] Video size ({file_size_mb:.2f} MB) exceeds limit, compressing"
            )
            compressed_path = os.path.join(job_dir, "final_video_compressed.mp4")
            ffmpeg_util.compress_video(
                final_path,
                compressed_path,
                max_size_mb=Config.MAX_VIDEO_SIZE_MB
            )
            return compressed_path
        
        return final_path
        
    except Exception as e:
        logger.error(f"[{job_id}] Video assembly failed: {e}")
        raise VideoGenerationError(f"Failed to assemble video: {e}") from e


def _handle_cancellation(
    job_id: str,
    file_manager: FileManager,
    notification_service: NotificationService,
    chat_id: int,
    stage: str
):
    """Handle job cancellation."""
    logger.info(f"[{job_id}] Handling cancellation at stage: {stage}")
    
    # Cleanup files
    try:
        file_manager.cleanup_job(job_id)
    except Exception as e:
        logger.error(f"[{job_id}] Cleanup failed during cancellation: {e}")
    
    # Send cancellation notification
    asyncio.run(notification_service.send_status_update(chat_id, JobStatus.CANCELLED, job_id))
    asyncio.run(notification_service.send_error_message(chat_id, "approval_timeout", job_id))


# ========== Helper Functions for Error Mapping ==========

def _map_exception_to_error_type(exception: Exception) -> str:
    """
    Map exception to user-friendly error type.
    
    Args:
        exception: The exception that occurred
        
    Returns:
        Error type key for ERROR_MESSAGES in NotificationService
    """
    error_message = str(exception).lower()
    exception_type = type(exception).__name__
    
    # OpenAI errors
    if "rate" in error_message and "limit" in error_message:
        return "openai_rate_limit"
    elif "openai" in error_message or exception_type == "OpenAIServiceError":
        return "openai_api_error"
    
    # Runway errors
    elif "timeout" in error_message and "runway" in error_message:
        return "runway_timeout"
    elif "runway" in error_message:
        return "runway_api_error"
    
    # FFmpeg errors
    elif "ffmpeg" in error_message:
        return "ffmpeg_error"
    
    # File errors
    elif "file" in error_message or "path" in error_message:
        return "file_error"
    
    # Transcription errors
    elif "transcrib" in error_message or "whisper" in error_message:
        return "transcription_error"
    
    # Default
    else:
        return "general_error"
