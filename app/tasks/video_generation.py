"""
Video Generation Task for AI Video Generator Bot.

Main Celery task that orchestrates the complete video generation pipeline
with user approval stages for script, images, and videos.
"""

import logging
import structlog
import os
import time
from typing import Optional
from redis import Redis

from app.tasks import celery_app
from app.config import Config
from app.models.video_job import VideoJob, JobStatus
from app.services.openai_service import OpenAIService, OpenAIServiceError
from app.services.runway_service import RunwayService
from app.services.script_service import ScriptService
from app.services.video_service import VideoService
from app.services.audio_service import AudioService
from app.services.approval_service import ApprovalManager
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
    
    # Initialize Redis and approval manager
    redis_client = Redis.from_url(Config.REDIS_URL, decode_responses=False)
    approval_manager = ApprovalManager(redis_client)
    
    # Create job directory
    job_dir = file_manager.create_job_directory(job_id)
    
    # Track metrics for each stage
    metrics = {
        "job_id": job_id,
        "stages": {}
    }
    
    try:
        # ========== STAGE 1: Generate Script ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="generate_script", stage_number=1)
        _send_status_notification(chat_id, JobStatus.GENERATING_SCRIPT)
        
        script = _generate_script(openai_service, prompt, job_id)
        
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
        _send_status_notification(chat_id, JobStatus.AWAITING_SCRIPT_APPROVAL)
        _send_script_approval_request(chat_id, job_id, script)
        
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
            _handle_cancellation(job_id, file_manager, chat_id, "script")
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
        _send_status_notification(chat_id, JobStatus.SCRIPT_APPROVED)
        
        # ========== STAGE 3: Generate Images ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="generate_images", stage_number=3)
        _send_status_notification(chat_id, JobStatus.GENERATING_IMAGES)
        
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
        _send_status_notification(chat_id, JobStatus.AWAITING_IMAGES_APPROVAL)
        
        # Get first 5 image paths for preview
        preview_images = [
            seg.image_path for seg in video_segments[:5]
            if seg.image_path
        ]
        _send_images_approval_request(chat_id, job_id, preview_images)
        
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
            _handle_cancellation(job_id, file_manager, chat_id, "images")
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
        _send_status_notification(chat_id, JobStatus.IMAGES_APPROVED)
        
        # ========== STAGE 5: Animate Videos ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="animate_videos", stage_number=5)
        _send_status_notification(chat_id, JobStatus.ANIMATING_VIDEOS)
        
        video_segments = _animate_videos(
            video_service,
            runway_service,
            job_id,
            video_segments,
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
        _send_status_notification(chat_id, JobStatus.AWAITING_VIDEOS_APPROVAL)
        
        # Get first 3 video paths for preview
        preview_videos = [
            seg.video_path for seg in video_segments[:3]
            if seg.video_path
        ]
        _send_videos_approval_request(chat_id, job_id, preview_videos)
        
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
            _handle_cancellation(job_id, file_manager, chat_id, "videos")
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
        _send_status_notification(chat_id, JobStatus.VIDEOS_APPROVED)
        
        # ========== STAGE 7: Generate Audio ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="generate_audio", stage_number=7)
        _send_status_notification(chat_id, JobStatus.GENERATING_AUDIO)
        
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
        _send_status_notification(chat_id, JobStatus.ASSEMBLING_VIDEO)
        
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
        _send_final_video(chat_id, final_video_path)
        _send_status_notification(chat_id, JobStatus.COMPLETED)
        
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
        _send_error_notification(chat_id, e)
        
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
    chat_id: int
):
    """Generate images for all segments with progress updates."""
    
    def progress_callback(current: int, total: int):
        """Send progress update to user every 10 segments."""
        if current % Config.PROGRESS_UPDATE_INTERVAL == 0:
            _send_progress_notification(chat_id, current, total, "images")
    
    try:
        # Note: This generates both images AND videos in parallel
        # We'll need to modify this to only generate images first
        video_segments = []
        
        for segment in segments:
            # Generate only the image part
            video_segment = video_service.generate_segment(job_id, segment)
            video_segments.append(video_segment)
            
            # Send progress update
            if len(video_segments) % Config.PROGRESS_UPDATE_INTERVAL == 0:
                progress_callback(len(video_segments), len(segments))
        
        return video_segments
        
    except Exception as e:
        logger.error(f"[{job_id}] Image generation failed: {e}")
        raise VideoGenerationError(f"Failed to generate images: {e}") from e


def _animate_videos(
    video_service: VideoService,
    runway_service: RunwayService,
    job_id: str,
    video_segments,
    chat_id: int
):
    """Animate all video segments with progress updates."""
    
    def progress_callback(current: int, total: int):
        """Send progress update to user every 10 segments."""
        if current % Config.PROGRESS_UPDATE_INTERVAL == 0:
            _send_progress_notification(chat_id, current, total, "videos")
    
    try:
        # Animation is already done in generate_segment
        # This is a placeholder for the actual animation logic
        # In a real implementation, we'd separate image generation from animation
        
        for i, segment in enumerate(video_segments):
            if (i + 1) % Config.PROGRESS_UPDATE_INTERVAL == 0:
                progress_callback(i + 1, len(video_segments))
        
        return video_segments
        
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
    _send_cancellation_notification(chat_id, stage)


# ========== Notification Functions ==========
# These are placeholders - actual implementation will be in bot/notifications.py

def _send_status_notification(chat_id: int, status: JobStatus):
    """Send status update to user."""
    # TODO: Implement via bot/notifications.py
    logger.info(f"Status notification: chat_id={chat_id}, status={status.value}")


def _send_progress_notification(chat_id: int, current: int, total: int, stage: str):
    """Send progress update to user."""
    # TODO: Implement via bot/notifications.py
    percentage = int((current / total) * 100)
    logger.info(
        f"Progress notification: chat_id={chat_id}, "
        f"stage={stage}, progress={current}/{total} ({percentage}%)"
    )


def _send_script_approval_request(chat_id: int, job_id: str, script: str):
    """Send script with approval buttons."""
    # TODO: Implement via bot/notifications.py
    logger.info(f"Script approval request: chat_id={chat_id}, job_id={job_id}")


def _send_images_approval_request(chat_id: int, job_id: str, image_paths: list):
    """Send image preview with approval buttons."""
    # TODO: Implement via bot/notifications.py
    logger.info(
        f"Images approval request: chat_id={chat_id}, "
        f"job_id={job_id}, images={len(image_paths)}"
    )


def _send_videos_approval_request(chat_id: int, job_id: str, video_paths: list):
    """Send video preview with approval buttons."""
    # TODO: Implement via bot/notifications.py
    logger.info(
        f"Videos approval request: chat_id={chat_id}, "
        f"job_id={job_id}, videos={len(video_paths)}"
    )


def _send_final_video(chat_id: int, video_path: str):
    """Send final video to user."""
    # TODO: Implement via bot/notifications.py
    logger.info(f"Sending final video: chat_id={chat_id}, path={video_path}")


def _send_error_notification(chat_id: int, error: Exception):
    """Send error notification to user."""
    # TODO: Implement via bot/notifications.py
    logger.info(f"Error notification: chat_id={chat_id}, error={type(error).__name__}")


def _send_cancellation_notification(chat_id: int, stage: str):
    """Send cancellation notification to user."""
    # TODO: Implement via bot/notifications.py
    logger.info(f"Cancellation notification: chat_id={chat_id}, stage={stage}")
