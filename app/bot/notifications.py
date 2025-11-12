"""
Notification Service for AI Video Generator Bot.

This module handles all user notifications including:
- Status updates during video generation
- Progress updates with percentage
- Error messages with user-friendly text
- Final video delivery
- Approval requests for script, images, and videos with inline buttons
"""

import logging
from typing import List, Optional
from pathlib import Path

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
from telegram.error import TelegramError

from app.config import Config
from app.models.video_job import JobStatus


logger = logging.getLogger(__name__)


# Error messages dictionary with user-friendly texts
ERROR_MESSAGES = {
    "openai_rate_limit": (
        "⏳ Сервис OpenAI временно перегружен.\n\n"
        "Пожалуйста, попробуйте через несколько минут."
    ),
    "openai_api_error": (
        "❌ Ошибка при обращении к OpenAI API.\n\n"
        "Пожалуйста, попробуйте еще раз."
    ),
    "runway_timeout": (
        "⚠️ Генерация видео заняла слишком много времени.\n\n"
        "Попробуйте упростить описание или повторите попытку позже."
    ),
    "runway_api_error": (
        "❌ Ошибка при обращении к Runway API.\n\n"
        "Пожалуйста, попробуйте еще раз."
    ),
    "ffmpeg_error": (
        "❌ Ошибка при сборке видео.\n\n"
        "Пожалуйста, попробуйте еще раз."
    ),
    "file_error": (
        "❌ Ошибка при работе с файлами.\n\n"
        "Пожалуйста, попробуйте еще раз."
    ),
    "transcription_error": (
        "❌ Не удалось распознать голосовое сообщение.\n\n"
        "Пожалуйста, попробуйте записать сообщение заново или используйте текст."
    ),
    "video_too_large": (
        "⚠️ Размер видео превышает лимит Telegram (50 МБ).\n\n"
        "Попробую сжать видео..."
    ),
    "compression_failed": (
        "❌ Не удалось сжать видео до допустимого размера.\n\n"
        "Попробуйте упростить описание для создания более короткого видео."
    ),
    "approval_timeout": (
        "⏱️ Время ожидания утверждения истекло (10 минут).\n\n"
        "Задача автоматически отменена. Временные файлы удалены.\n\n"
        "Вы можете начать новую задачу, отправив новое описание."
    ),
    "general_error": (
        "❌ Произошла непредвиденная ошибка.\n\n"
        "Пожалуйста, попробуйте еще раз или обратитесь в поддержку."
    ),
}


# Status messages for different job states
STATUS_MESSAGES = {
    JobStatus.GENERATING_SCRIPT: "📝 Генерирую сценарий для вашего видео...",
    JobStatus.AWAITING_SCRIPT_APPROVAL: "⏸️ Ожидаю утверждения сценария...",
    JobStatus.SCRIPT_APPROVED: "✅ Сценарий утвержден!",
    JobStatus.GENERATING_IMAGES: "🎨 Создаю изображения для видео...",
    JobStatus.AWAITING_IMAGES_APPROVAL: "⏸️ Ожидаю утверждения изображений...",
    JobStatus.IMAGES_APPROVED: "✅ Изображения утверждены!",
    JobStatus.ANIMATING_VIDEOS: "🎬 Анимирую видео сегменты...",
    JobStatus.AWAITING_VIDEOS_APPROVAL: "⏸️ Ожидаю утверждения видео...",
    JobStatus.VIDEOS_APPROVED: "✅ Видео утверждены!",
    JobStatus.GENERATING_AUDIO: "🎵 Генерирую озвучку...",
    JobStatus.ASSEMBLING_VIDEO: "🎞️ Собираю финальное видео...",
    JobStatus.COMPLETED: "✅ Видео готово!",
    JobStatus.CANCELLED: "❌ Задача отменена.",
    JobStatus.FAILED: "❌ Задача завершилась с ошибкой.",
}


class NotificationService:
    """Service for sending notifications to users via Telegram bot."""
    
    def __init__(self, bot_token: Optional[str] = None):
        """
        Initialize notification service with Telegram bot.
        
        Args:
            bot_token: Telegram bot token (uses Config.TELEGRAM_BOT_TOKEN if not provided)
        """
        self.bot_token = bot_token or Config.TELEGRAM_BOT_TOKEN
        
        if not self.bot_token:
            raise ValueError("Telegram bot token is required")
        
        self.bot = Bot(token=self.bot_token)
        
        logger.info("NotificationService initialized")
    
    async def send_status_update(
        self,
        chat_id: int,
        status: JobStatus,
        job_id: Optional[str] = None
    ) -> None:
        """
        Send status update message to user.
        
        Args:
            chat_id: Telegram chat ID
            status: Current job status
            job_id: Optional job identifier for logging
        """
        message = STATUS_MESSAGES.get(
            status,
            f"📊 Статус: {status.value}"
        )
        
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message
            )
            
            logger.info(
                f"Status update sent: chat_id={chat_id}, status={status.value}, "
                f"job_id={job_id}"
            )
            
        except TelegramError as e:
            logger.error(
                f"Failed to send status update: chat_id={chat_id}, "
                f"status={status.value}, job_id={job_id}, error={str(e)}",
                exc_info=True
            )
    
    async def send_progress_update(
        self,
        chat_id: int,
        current: int,
        total: int,
        stage: str = "обработки",
        job_id: Optional[str] = None
    ) -> None:
        """
        Send progress update with percentage.
        
        Args:
            chat_id: Telegram chat ID
            current: Current progress count
            total: Total count
            stage: Stage name (e.g., "генерации изображений", "анимации")
            job_id: Optional job identifier for logging
        """
        if total == 0:
            logger.warning(
                f"Invalid progress update: total=0, chat_id={chat_id}, job_id={job_id}"
            )
            return
        
        percentage = int((current / total) * 100)
        
        # Create progress bar
        bar_length = 10
        filled_length = int(bar_length * current / total)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        message = (
            f"⏳ Прогресс {stage}:\n\n"
            f"{bar} {percentage}%\n\n"
            f"Обработано: {current} из {total}"
        )
        
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message
            )
            
            logger.info(
                f"Progress update sent: chat_id={chat_id}, "
                f"progress={current}/{total} ({percentage}%), "
                f"stage={stage}, job_id={job_id}"
            )
            
        except TelegramError as e:
            logger.error(
                f"Failed to send progress update: chat_id={chat_id}, "
                f"progress={current}/{total}, job_id={job_id}, error={str(e)}",
                exc_info=True
            )
    
    async def send_error_message(
        self,
        chat_id: int,
        error_type: str,
        job_id: Optional[str] = None,
        additional_info: Optional[str] = None
    ) -> None:
        """
        Send user-friendly error message.
        
        Args:
            chat_id: Telegram chat ID
            error_type: Error type key from ERROR_MESSAGES
            job_id: Optional job identifier for logging
            additional_info: Optional additional information to append
        """
        message = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES["general_error"])
        
        if additional_info:
            message += f"\n\n{additional_info}"
        
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message
            )
            
            logger.info(
                f"Error message sent: chat_id={chat_id}, "
                f"error_type={error_type}, job_id={job_id}"
            )
            
        except TelegramError as e:
            logger.error(
                f"Failed to send error message: chat_id={chat_id}, "
                f"error_type={error_type}, job_id={job_id}, error={str(e)}",
                exc_info=True
            )
    
    async def send_final_video(
        self,
        chat_id: int,
        video_path: str,
        job_id: Optional[str] = None,
        caption: Optional[str] = None,
        duration_seconds: Optional[int] = None
    ) -> None:
        """
        Send final video to user.
        
        Args:
            chat_id: Telegram chat ID
            video_path: Path to video file
            job_id: Optional job identifier for logging
            caption: Optional video caption
            duration_seconds: Optional generation duration for caption
        """
        # Check if file exists
        video_file = Path(video_path)
        if not video_file.exists():
            logger.error(
                f"Video file not found: path={video_path}, "
                f"chat_id={chat_id}, job_id={job_id}"
            )
            await self.send_error_message(chat_id, "file_error", job_id)
            return
        
        # Get file size
        file_size_mb = video_file.stat().st_size / (1024 * 1024)
        
        # Build caption
        if not caption:
            caption = "🎉 Ваше видео готово!"
            if duration_seconds:
                minutes = duration_seconds // 60
                seconds = duration_seconds % 60
                caption += f"\n\n⏱️ Время генерации: {minutes}м {seconds}с"
            caption += f"\n📦 Размер: {file_size_mb:.1f} МБ"
        
        try:
            with open(video_path, 'rb') as video_file:
                await self.bot.send_video(
                    chat_id=chat_id,
                    video=video_file,
                    caption=caption,
                    supports_streaming=True
                )
            
            logger.info(
                f"Final video sent: chat_id={chat_id}, "
                f"size={file_size_mb:.2f} MB, job_id={job_id}"
            )
            
        except TelegramError as e:
            logger.error(
                f"Failed to send final video: chat_id={chat_id}, "
                f"video_path={video_path}, job_id={job_id}, error={str(e)}",
                exc_info=True
            )
            
            # Try to send error message
            await self.send_error_message(
                chat_id,
                "general_error",
                job_id,
                "Не удалось отправить видео. Пожалуйста, обратитесь в поддержку."
            )

    async def send_script_approval(
        self,
        chat_id: int,
        job_id: str,
        script: str
    ) -> None:
        """
        Send script for approval with inline buttons.
        
        Args:
            chat_id: Telegram chat ID
            job_id: Job identifier for callback data
            script: Generated script text
        """
        # Truncate script if too long (Telegram message limit is 4096 characters)
        max_script_length = 3500  # Leave room for header and buttons
        truncated = False
        
        if len(script) > max_script_length:
            script = script[:max_script_length] + "..."
            truncated = True
        
        # Build message
        message = (
            "📝 Сценарий готов!\n\n"
            "Пожалуйста, ознакомьтесь с сценарием и утвердите его для продолжения:\n\n"
            "─────────────────────\n\n"
            f"{script}\n\n"
            "─────────────────────\n"
        )
        
        if truncated:
            message += "\n⚠️ Сценарий слишком длинный и был сокращен для отображения.\n"
        
        message += (
            "\n💡 Если сценарий вас устраивает, нажмите \"✅ Утвердить\".\n"
            "Если хотите начать заново, нажмите \"❌ Отменить\"."
        )
        
        # Create inline keyboard
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ Утвердить",
                    callback_data=f"approve_script:{job_id}"
                ),
                InlineKeyboardButton(
                    "❌ Отменить",
                    callback_data=f"cancel_script:{job_id}"
                )
            ]
        ])
        
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                reply_markup=keyboard
            )
            
            logger.info(
                f"Script approval request sent: chat_id={chat_id}, "
                f"job_id={job_id}, script_length={len(script)}"
            )
            
        except TelegramError as e:
            logger.error(
                f"Failed to send script approval: chat_id={chat_id}, "
                f"job_id={job_id}, error={str(e)}",
                exc_info=True
            )
    
    async def send_images_approval(
        self,
        chat_id: int,
        job_id: str,
        image_paths: List[str]
    ) -> None:
        """
        Send gallery of first 5 images for approval with inline buttons.
        
        Args:
            chat_id: Telegram chat ID
            job_id: Job identifier for callback data
            image_paths: List of paths to generated images
        """
        # Take first 5 images for preview
        preview_images = image_paths[:5]
        
        # Check if files exist
        valid_images = []
        for img_path in preview_images:
            if Path(img_path).exists():
                valid_images.append(img_path)
            else:
                logger.warning(
                    f"Image file not found: path={img_path}, "
                    f"chat_id={chat_id}, job_id={job_id}"
                )
        
        if not valid_images:
            logger.error(
                f"No valid images found for approval: chat_id={chat_id}, job_id={job_id}"
            )
            await self.send_error_message(chat_id, "file_error", job_id)
            return
        
        # Build caption
        caption = (
            f"🎨 Изображения готовы!\n\n"
            f"Показываю первые {len(valid_images)} из {len(image_paths)} изображений.\n\n"
            f"💡 Если изображения вас устраивают, нажмите \"✅ Утвердить изображения\".\n"
            f"Если хотите начать заново, нажмите \"❌ Отменить\"."
        )
        
        # Create inline keyboard
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ Утвердить изображения",
                    callback_data=f"approve_images:{job_id}"
                ),
                InlineKeyboardButton(
                    "❌ Отменить",
                    callback_data=f"cancel_images:{job_id}"
                )
            ]
        ])
        
        try:
            # Send images as media group
            media_group = []
            for i, img_path in enumerate(valid_images):
                with open(img_path, 'rb') as img_file:
                    # Add caption only to first image
                    if i == 0:
                        media_group.append(
                            InputMediaPhoto(
                                media=img_file.read(),
                                caption=caption
                            )
                        )
                    else:
                        media_group.append(
                            InputMediaPhoto(media=img_file.read())
                        )
            
            # Send media group
            await self.bot.send_media_group(
                chat_id=chat_id,
                media=media_group
            )
            
            # Send keyboard in separate message (media groups don't support reply_markup)
            await self.bot.send_message(
                chat_id=chat_id,
                text="Выберите действие:",
                reply_markup=keyboard
            )
            
            logger.info(
                f"Images approval request sent: chat_id={chat_id}, "
                f"job_id={job_id}, images_count={len(valid_images)}"
            )
            
        except TelegramError as e:
            logger.error(
                f"Failed to send images approval: chat_id={chat_id}, "
                f"job_id={job_id}, error={str(e)}",
                exc_info=True
            )
    
    async def send_videos_approval(
        self,
        chat_id: int,
        job_id: str,
        video_paths: List[str]
    ) -> None:
        """
        Send first 3 video segments for approval with inline buttons.
        
        Args:
            chat_id: Telegram chat ID
            job_id: Job identifier for callback data
            video_paths: List of paths to generated video segments
        """
        # Take first 3 videos for preview
        preview_videos = video_paths[:3]
        
        # Check if files exist
        valid_videos = []
        for vid_path in preview_videos:
            if Path(vid_path).exists():
                valid_videos.append(vid_path)
            else:
                logger.warning(
                    f"Video file not found: path={vid_path}, "
                    f"chat_id={chat_id}, job_id={job_id}"
                )
        
        if not valid_videos:
            logger.error(
                f"No valid videos found for approval: chat_id={chat_id}, job_id={job_id}"
            )
            await self.send_error_message(chat_id, "file_error", job_id)
            return
        
        # Build caption
        caption = (
            f"🎬 Видео сегменты готовы!\n\n"
            f"Показываю первые {len(valid_videos)} из {len(video_paths)} видео.\n\n"
            f"💡 Если видео вас устраивают, нажмите \"✅ Утвердить видео\".\n"
            f"Если хотите начать заново, нажмите \"❌ Отменить\"."
        )
        
        # Create inline keyboard
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ Утвердить видео",
                    callback_data=f"approve_videos:{job_id}"
                ),
                InlineKeyboardButton(
                    "❌ Отменить",
                    callback_data=f"cancel_videos:{job_id}"
                )
            ]
        ])
        
        try:
            # Send videos as media group
            media_group = []
            for i, vid_path in enumerate(valid_videos):
                with open(vid_path, 'rb') as vid_file:
                    # Add caption only to first video
                    if i == 0:
                        media_group.append(
                            InputMediaVideo(
                                media=vid_file.read(),
                                caption=caption,
                                supports_streaming=True
                            )
                        )
                    else:
                        media_group.append(
                            InputMediaVideo(
                                media=vid_file.read(),
                                supports_streaming=True
                            )
                        )
            
            # Send media group
            await self.bot.send_media_group(
                chat_id=chat_id,
                media=media_group
            )
            
            # Send keyboard in separate message (media groups don't support reply_markup)
            await self.bot.send_message(
                chat_id=chat_id,
                text="Выберите действие:",
                reply_markup=keyboard
            )
            
            logger.info(
                f"Videos approval request sent: chat_id={chat_id}, "
                f"job_id={job_id}, videos_count={len(valid_videos)}"
            )
            
        except TelegramError as e:
            logger.error(
                f"Failed to send videos approval: chat_id={chat_id}, "
                f"job_id={job_id}, error={str(e)}",
                exc_info=True
            )
