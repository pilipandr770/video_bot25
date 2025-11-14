"""
Enhanced Video Generation Pipeline with detailed step tracking.
Uses all three OpenAI Assistants and stores intermediate data in database.
"""

import logging
import structlog
import os
import time
import asyncio
from typing import Optional, List
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

from app.tasks import celery_app
from app.config import Config
from app.models.database import get_db_session
from app.models.video_job_enhanced import VideoJobEnhanced, VideoSegmentEnhanced
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


@celery_app.task(bind=True, max_retries=3, name='app.tasks.generate_video_enhanced')
def generate_video_enhanced_task(
    self,
    job_id: str,
    user_id: int,
    chat_id: int,
    prompt: str
) -> dict:
    """
    Enhanced video generation pipeline with detailed tracking.
    
    Pipeline stages:
    1. Generate script via Script Assistant
    2. ⏸️ Wait for script approval
    3. Generate image prompts via Segment Assistant (10 prompts)
    4. Generate images via Runway API (10 images)
    5. ⏸️ Wait for images approval
    6. Generate animation prompts via Animation Assistant (10 prompts)
    7. Animate images via Runway API (10 videos)
    8. ⏸️ Wait for videos approval
    9. Generate audio via OpenAI TTS
    10. Assemble final video via FFmpeg
    11. Send final video to user
    12. Cleanup temporary files
    
    Args:
        job_id: Unique identifier for the job
        user_id: Telegram user ID
        chat_id: Telegram chat ID
        prompt: User's video description
        
    Returns:
        dict: Job result with status and paths
    """
    job_start_time = time.time()
    
    logger.info(
        "enhanced_video_generation_started",
        job_id=job_id,
        user_id=user_id,
        chat_id=chat_id,
        prompt_length=len(prompt)
    )
    
    # Initialize services
    file_manager = FileManager()
    openai_service = OpenAIService()
    runway_service = RunwayService(Config.RUNWAY_API_KEY)
    script_service = ScriptService(
        target_duration=Config.TARGET_VIDEO_DURATION,
        segment_duration=Config.SEGMENT_DURATION
    )
    video_service = VideoService(runway_service, script_service, file_manager)
    audio_service = AudioService(openai_service)
    ffmpeg_util = FFmpegUtil()
    notification_service = NotificationService()
    approval_manager = ApprovalManager()
    
    # Create job directory
    job_dir = file_manager.create_job_directory(job_id)
    
    # Create database session
    db = get_db_session()
    
    try:
        # ========== STAGE 0: Create Job in Database ==========
        video_job = VideoJobEnhanced(
            id=job_id,
            user_id=user_id,
            chat_id=chat_id,
            prompt=prompt,
            status='processing'
        )
        db.add(video_job)
        db.commit()
        logger.info("enhanced_job_created_in_db", job_id=job_id)
        
        # ========== STAGE 1: Generate Script ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="generate_script", stage_number=1)
        asyncio.run(notification_service.send_status_update(chat_id, "generating_script", job_id))
        
        script = openai_service.generate_script(prompt)
        
        # Save script to database
        video_job.script_text = script
        video_job.script_generated_at = datetime.utcnow()
        video_job.status = 'awaiting_script_approval'
        db.commit()
        
        stage_duration = time.time() - stage_start
        logger.info(
            "stage_completed",
            job_id=job_id,
            stage="generate_script",
            duration_seconds=round(stage_duration, 2),
            script_length=len(script)
        )
        
        # ========== STAGE 2: Script Approval ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="script_approval", stage_number=2)
        asyncio.run(notification_service.send_script_approval(chat_id, job_id, script))
        
        approved = approval_manager.wait_for_approval(
            job_id,
            'script',
            timeout=Config.APPROVAL_TIMEOUT
        )
        
        if not approved:
            logger.info("job_cancelled", job_id=job_id, stage="script_approval")
            video_job.status = 'cancelled'
            video_job.script_approved = -1
            db.commit()
            _handle_cancellation(job_id, file_manager, notification_service, chat_id, "script")
            return {"status": "cancelled", "stage": "script_approval"}
        
        video_job.script_approved = 1
        video_job.status = 'script_approved'
        db.commit()
        
        logger.info("stage_completed", job_id=job_id, stage="script_approval")
        asyncio.run(notification_service.send_message(chat_id, "✅ Сценарий утверждён! Начинаю генерацию..."))
        
        # ========== STAGE 3: Split Script into Segments ==========
        logger.info("stage_started", job_id=job_id, stage="split_script", stage_number=3)
        
        segments = script_service.split_script(script)
        
        # Create segment records in database
        for seg in segments:
            db_segment = VideoSegmentEnhanced(
                job_id=job_id,
                segment_index=seg.index,
                text=seg.text,
                start_time=seg.start_time,
                end_time=seg.end_time,
                status='pending'
            )
            db.add(db_segment)
        db.commit()
        
        logger.info(
            "stage_completed",
            job_id=job_id,
            stage="split_script",
            segment_count=len(segments)
        )
        
        # ========== STAGE 4: Generate Image Prompts ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="generate_image_prompts", stage_number=4)
        asyncio.run(notification_service.send_message(
            chat_id,
            f"📝 Генерирую промпты для изображений (0/{Config.NUM_SEGMENTS})..."
        ))
        
        db_segments = db.query(VideoSegmentEnhanced).filter_by(job_id=job_id).order_by(VideoSegmentEnhanced.segment_index).all()
        
        for i, db_seg in enumerate(db_segments):
            logger.info(
                "generating_image_prompt",
                job_id=job_id,
                segment_index=db_seg.segment_index,
                progress=f"{i+1}/{len(db_segments)}"
            )
            
            image_prompt = openai_service.generate_image_prompt(db_seg.text)
            
            db_seg.image_prompt = image_prompt
            db_seg.image_prompt_generated_at = datetime.utcnow()
            db_seg.status = 'image_prompt_ready'
            db.commit()
            
            # Update progress every 2 prompts
            if (i + 1) % 2 == 0 or i == len(db_segments) - 1:
                asyncio.run(notification_service.send_message(
                    chat_id,
                    f"📝 Промпты для изображений: {i+1}/{len(db_segments)}"
                ))
        
        stage_duration = time.time() - stage_start
        logger.info(
            "stage_completed",
            job_id=job_id,
            stage="generate_image_prompts",
            duration_seconds=round(stage_duration, 2),
            prompts_generated=len(db_segments)
        )
        
        # ========== STAGE 5: Generate Images ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="generate_images", stage_number=5)
        asyncio.run(notification_service.send_message(
            chat_id,
            f"🎨 Генерирую изображения (0/{Config.NUM_SEGMENTS})..."
        ))
        
        for i, db_seg in enumerate(db_segments):
            logger.info(
                "generating_image",
                job_id=job_id,
                segment_index=db_seg.segment_index,
                progress=f"{i+1}/{len(db_segments)}"
            )
            
            # Generate image using Runway
            image_path = os.path.join(job_dir, "images", f"segment_{db_seg.segment_index:02d}.png")
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            
            task_id = runway_service.generate_image(
                prompt=db_seg.image_prompt,
                output_path=image_path
            )
            
            db_seg.image_path = image_path
            db_seg.image_runway_task_id = task_id
            db_seg.image_generated_at = datetime.utcnow()
            db_seg.status = 'image_ready'
            db.commit()
            
            # Update progress
            asyncio.run(notification_service.send_message(
                chat_id,
                f"🎨 Изображения: {i+1}/{len(db_segments)}"
            ))
        
        stage_duration = time.time() - stage_start
        logger.info(
            "stage_completed",
            job_id=job_id,
            stage="generate_images",
            duration_seconds=round(stage_duration, 2),
            images_generated=len(db_segments)
        )
        
        # ========== STAGE 6: Images Approval ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="images_approval", stage_number=6)
        
        # Send first 5 images for preview
        preview_images = [seg.image_path for seg in db_segments[:5] if seg.image_path]
        asyncio.run(notification_service.send_images_approval(chat_id, job_id, preview_images))
        
        approved = approval_manager.wait_for_approval(
            job_id,
            'images',
            timeout=Config.APPROVAL_TIMEOUT
        )
        
        if not approved:
            logger.info("job_cancelled", job_id=job_id, stage="images_approval")
            video_job.status = 'cancelled'
            db.commit()
            _handle_cancellation(job_id, file_manager, notification_service, chat_id, "images")
            return {"status": "cancelled", "stage": "images_approval"}
        
        video_job.status = 'images_approved'
        db.commit()
        
        logger.info("stage_completed", job_id=job_id, stage="images_approval")
        asyncio.run(notification_service.send_message(chat_id, "✅ Изображения утверждены! Начинаю анимацию..."))
        
        # ========== STAGE 7: Generate Animation Prompts ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="generate_animation_prompts", stage_number=7)
        asyncio.run(notification_service.send_message(
            chat_id,
            f"📝 Генерирую промпты для анимации (0/{Config.NUM_SEGMENTS})..."
        ))
        
        for i, db_seg in enumerate(db_segments):
            logger.info(
                "generating_animation_prompt",
                job_id=job_id,
                segment_index=db_seg.segment_index,
                progress=f"{i+1}/{len(db_segments)}"
            )
            
            animation_prompt = openai_service.generate_animation_prompt(db_seg.text)
            
            db_seg.animation_prompt = animation_prompt
            db_seg.animation_prompt_generated_at = datetime.utcnow()
            db_seg.status = 'animation_prompt_ready'
            db.commit()
            
            # Update progress every 2 prompts
            if (i + 1) % 2 == 0 or i == len(db_segments) - 1:
                asyncio.run(notification_service.send_message(
                    chat_id,
                    f"📝 Промпты для анимации: {i+1}/{len(db_segments)}"
                ))
        
        stage_duration = time.time() - stage_start
        logger.info(
            "stage_completed",
            job_id=job_id,
            stage="generate_animation_prompts",
            duration_seconds=round(stage_duration, 2),
            prompts_generated=len(db_segments)
        )
        
        # ========== STAGE 8: Animate Videos ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="animate_videos", stage_number=8)
        asyncio.run(notification_service.send_message(
            chat_id,
            f"🎬 Анимирую видео (0/{Config.NUM_SEGMENTS})..."
        ))
        
        for i, db_seg in enumerate(db_segments):
            logger.info(
                "animating_video",
                job_id=job_id,
                segment_index=db_seg.segment_index,
                progress=f"{i+1}/{len(db_segments)}"
            )
            
            # Animate image using Runway
            video_path = os.path.join(job_dir, "videos", f"segment_{db_seg.segment_index:02d}.mp4")
            os.makedirs(os.path.dirname(video_path), exist_ok=True)
            
            task_id = runway_service.animate_image(
                image_path=db_seg.image_path,
                prompt=db_seg.animation_prompt,
                output_path=video_path,
                duration=Config.SEGMENT_DURATION
            )
            
            db_seg.video_path = video_path
            db_seg.video_runway_task_id = task_id
            db_seg.video_duration = Config.SEGMENT_DURATION
            db_seg.video_generated_at = datetime.utcnow()
            db_seg.status = 'video_ready'
            db.commit()
            
            # Update progress
            asyncio.run(notification_service.send_message(
                chat_id,
                f"🎬 Видео: {i+1}/{len(db_segments)}"
            ))
        
        stage_duration = time.time() - stage_start
        logger.info(
            "stage_completed",
            job_id=job_id,
            stage="animate_videos",
            duration_seconds=round(stage_duration, 2),
            videos_generated=len(db_segments)
        )
        
        # ========== STAGE 9: Videos Approval ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="videos_approval", stage_number=9)
        
        # Send first 3 videos for preview
        preview_videos = [seg.video_path for seg in db_segments[:3] if seg.video_path]
        asyncio.run(notification_service.send_videos_approval(chat_id, job_id, preview_videos))
        
        approved = approval_manager.wait_for_approval(
            job_id,
            'videos',
            timeout=Config.APPROVAL_TIMEOUT
        )
        
        if not approved:
            logger.info("job_cancelled", job_id=job_id, stage="videos_approval")
            video_job.status = 'cancelled'
            db.commit()
            _handle_cancellation(job_id, file_manager, notification_service, chat_id, "videos")
            return {"status": "cancelled", "stage": "videos_approval"}
        
        video_job.status = 'videos_approved'
        db.commit()
        
        logger.info("stage_completed", job_id=job_id, stage="videos_approval")
        asyncio.run(notification_service.send_message(chat_id, "✅ Видео утверждены! Финальная сборка..."))
        
        # ========== STAGE 10: Generate Audio ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="generate_audio", stage_number=10)
        asyncio.run(notification_service.send_message(chat_id, "🎤 Генерирую озвучку..."))
        
        audio_path = os.path.join(job_dir, "audio", "voiceover.mp3")
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        
        audio_service.generate_audio(
            script=script,
            output_path=audio_path,
            target_duration=Config.TARGET_VIDEO_DURATION
        )
        
        audio_duration = ffmpeg_util.get_audio_duration(audio_path) if os.path.exists(audio_path) else 0
        
        video_job.audio_path = audio_path
        video_job.audio_duration = audio_duration
        db.commit()
        
        stage_duration = time.time() - stage_start
        logger.info(
            "stage_completed",
            job_id=job_id,
            stage="generate_audio",
            duration_seconds=round(stage_duration, 2),
            audio_duration=round(audio_duration, 2)
        )
        
        # ========== STAGE 11: Assemble Final Video ==========
        stage_start = time.time()
        logger.info("stage_started", job_id=job_id, stage="assemble_video", stage_number=11)
        asyncio.run(notification_service.send_message(chat_id, "🎬 Собираю финальное видео..."))
        
        # Get all video paths in order
        video_paths = [seg.video_path for seg in db_segments if seg.video_path]
        
        # Concatenate videos
        concatenated_path = os.path.join(job_dir, "concatenated.mp4")
        ffmpeg_util.concatenate_videos(video_paths, concatenated_path)
        
        # Add audio
        final_path = os.path.join(job_dir, "final_video.mp4")
        ffmpeg_util.add_audio(concatenated_path, audio_path, final_path)
        
        # Check file size and compress if needed
        file_size_mb = os.path.getsize(final_path) / (1024 * 1024)
        
        if file_size_mb > Config.MAX_VIDEO_SIZE_MB:
            logger.info(f"Video size ({file_size_mb:.2f} MB) exceeds limit, compressing")
            compressed_path = os.path.join(job_dir, "final_video_compressed.mp4")
            ffmpeg_util.compress_video(final_path, compressed_path, max_size_mb=Config.MAX_VIDEO_SIZE_MB)
            final_path = compressed_path
            file_size_mb = os.path.getsize(final_path) / (1024 * 1024)
        
        video_duration = ffmpeg_util.get_video_duration(final_path)
        
        video_job.final_video_path = final_path
        video_job.final_video_size_mb = file_size_mb
        video_job.final_video_duration = video_duration
        video_job.status = 'completed'
        video_job.completed_at = datetime.utcnow()
        db.commit()
        
        stage_duration = time.time() - stage_start
        logger.info(
            "stage_completed",
            job_id=job_id,
            stage="assemble_video",
            duration_seconds=round(stage_duration, 2),
            video_size_mb=round(file_size_mb, 2),
            video_duration=round(video_duration, 2)
        )
        
        # ========== STAGE 12: Send Final Video ==========
        logger.info("stage_started", job_id=job_id, stage="send_video", stage_number=12)
        asyncio.run(notification_service.send_final_video(
            chat_id,
            final_path,
            job_id=job_id,
            duration_seconds=int(video_duration)
        ))
        
        logger.info("stage_completed", job_id=job_id, stage="send_video")
        
        # ========== STAGE 13: Cleanup ==========
        logger.info("stage_started", job_id=job_id, stage="cleanup", stage_number=13)
        file_manager.cleanup_job(job_id)
        logger.info("stage_completed", job_id=job_id, stage="cleanup")
        
        total_duration = time.time() - job_start_time
        logger.info(
            "enhanced_video_generation_completed",
            job_id=job_id,
            total_duration_seconds=round(total_duration, 2),
            total_duration_minutes=round(total_duration / 60, 2)
        )
        
        return {
            "status": "completed",
            "job_id": job_id,
            "final_video_path": final_path,
            "duration_seconds": total_duration
        }
        
    except Exception as e:
        logger.error(
            "enhanced_video_generation_failed",
            job_id=job_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        
        video_job.status = 'failed'
        db.commit()
        
        asyncio.run(notification_service.send_error_message(chat_id, "general_error", job_id))
        
        try:
            file_manager.cleanup_job(job_id)
        except Exception as cleanup_error:
            logger.error("cleanup_failed", job_id=job_id, error=str(cleanup_error))
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)
        
        raise VideoGenerationError(f"Video generation failed: {str(e)}") from e
        
    finally:
        db.close()


def _handle_cancellation(
    job_id: str,
    file_manager: FileManager,
    notification_service: NotificationService,
    chat_id: int,
    stage: str
):
    """Handle job cancellation."""
    logger.info(f"Handling cancellation at stage: {stage}", job_id=job_id)
    
    try:
        file_manager.cleanup_job(job_id)
    except Exception as e:
        logger.error(f"Cleanup failed during cancellation: {e}", job_id=job_id)
    
    asyncio.run(notification_service.send_message(
        chat_id,
        f"❌ Генерация отменена на этапе: {stage}"
    ))
