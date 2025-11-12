"""
Telegram Bot Handlers for AI Video Generator Bot.

This module contains all message handlers for the Telegram bot including:
- /start command handler
- Text message handler
- Voice message handler
- Callback query handler for approval buttons
"""

import logging
import uuid
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from redis import Redis

from app.config import Config
from app.services.approval_service import ApprovalManager
from app.tasks.video_generation import generate_video_task


logger = logging.getLogger(__name__)


# Initialize Redis client for approval manager
redis_client = Redis.from_url(Config.REDIS_URL, decode_responses=False)
approval_manager = ApprovalManager(redis_client)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command with welcome message.
    
    Sends a greeting message explaining how to use the bot.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(
        f"User started bot: user_id={user.id}, username={user.username}, chat_id={chat_id}"
    )
    
    welcome_message = (
        f"👋 Привет, {user.first_name}!\n\n"
        "Я бот для автоматической генерации рекламных видеороликов.\n\n"
        "📝 Отправьте мне текстовое или голосовое описание вашего рекламного ролика, "
        "и я создам для вас профессиональное 4-минутное видео с озвучкой.\n\n"
        "✨ Процесс включает несколько этапов:\n"
        "1️⃣ Генерация сценария\n"
        "2️⃣ Создание изображений\n"
        "3️⃣ Анимация видео\n"
        "4️⃣ Добавление озвучки\n"
        "5️⃣ Финальная сборка\n\n"
        "На каждом ключевом этапе вы сможете утвердить результат или отменить задачу.\n\n"
        "⏱️ Генерация занимает примерно 15-20 минут.\n\n"
        "Готовы начать? Отправьте описание вашего ролика!"
    )
    
    await update.message.reply_text(welcome_message)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle text messages from users.
    
    Validates the message, creates a video generation job, and starts
    the Celery task for processing.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    message = update.message
    
    # Validate message type
    if not message.text:
        logger.warning(
            f"Invalid message type received: user_id={user.id}, chat_id={chat_id}"
        )
        await message.reply_text(
            "❌ Пожалуйста, отправьте текстовое или голосовое сообщение с описанием ролика."
        )
        return
    
    prompt = message.text.strip()
    
    # Validate prompt is not empty
    if not prompt:
        await message.reply_text(
            "❌ Описание не может быть пустым. Пожалуйста, опишите ваш рекламный ролик."
        )
        return
    
    logger.info(
        f"Text message received: user_id={user.id}, chat_id={chat_id}, "
        f"prompt_length={len(prompt)}"
    )
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Start video generation task
    try:
        generate_video_task.delay(
            job_id=job_id,
            user_id=user.id,
            chat_id=chat_id,
            prompt=prompt
        )
        
        logger.info(
            f"Video generation task started: job_id={job_id}, "
            f"user_id={user.id}, chat_id={chat_id}"
        )
        
        # Send confirmation message with time estimate
        confirmation_message = (
            "✅ Ваш запрос принят!\n\n"
            f"🆔 ID задачи: `{job_id}`\n\n"
            "⏱️ Примерное время генерации: 15-20 минут\n\n"
            "Я буду отправлять вам обновления на каждом этапе. "
            "Вы сможете утвердить или отменить задачу после генерации сценария, "
            "изображений и видео.\n\n"
            "Начинаю работу... 🚀"
        )
        
        await message.reply_text(
            confirmation_message,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(
            f"Failed to start video generation task: job_id={job_id}, "
            f"user_id={user.id}, error={str(e)}",
            exc_info=True
        )
        
        await message.reply_text(
            "❌ Произошла ошибка при запуске задачи. "
            "Пожалуйста, попробуйте еще раз через несколько минут."
        )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle voice messages from users.
    
    Downloads the voice message, validates size, and starts the video
    generation task. The voice will be transcribed by the OpenAI service
    in the generation pipeline.
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    message = update.message
    voice = message.voice
    
    # Validate voice message
    if not voice:
        logger.warning(
            f"Invalid voice message: user_id={user.id}, chat_id={chat_id}"
        )
        await message.reply_text(
            "❌ Пожалуйста, отправьте голосовое сообщение с описанием ролика."
        )
        return
    
    # Validate voice size (max 20 MB)
    max_size_bytes = 20 * 1024 * 1024  # 20 MB
    if voice.file_size > max_size_bytes:
        logger.warning(
            f"Voice message too large: user_id={user.id}, "
            f"size={voice.file_size / (1024 * 1024):.2f} MB"
        )
        await message.reply_text(
            "❌ Голосовое сообщение слишком большое (максимум 20 МБ). "
            "Пожалуйста, отправьте более короткое сообщение или используйте текст."
        )
        return
    
    logger.info(
        f"Voice message received: user_id={user.id}, chat_id={chat_id}, "
        f"duration={voice.duration}s, size={voice.file_size / 1024:.2f} KB"
    )
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    try:
        # Download voice file
        voice_file = await voice.get_file()
        voice_bytes = await voice_file.download_as_bytearray()
        
        logger.info(
            f"Voice file downloaded: job_id={job_id}, size={len(voice_bytes)} bytes"
        )
        
        # For voice messages, we'll pass a special marker that the task will recognize
        # The actual transcription will happen in the video generation task
        prompt = f"__VOICE_MESSAGE__|{voice.file_id}"
        
        # Start video generation task
        generate_video_task.delay(
            job_id=job_id,
            user_id=user.id,
            chat_id=chat_id,
            prompt=prompt
        )
        
        logger.info(
            f"Video generation task started (voice): job_id={job_id}, "
            f"user_id={user.id}, chat_id={chat_id}"
        )
        
        # Send confirmation message
        confirmation_message = (
            "✅ Ваше голосовое сообщение принято!\n\n"
            f"🆔 ID задачи: `{job_id}`\n\n"
            "🎤 Сначала я распознаю вашу речь, затем начну генерацию видео.\n\n"
            "⏱️ Примерное время: 15-20 минут\n\n"
            "Начинаю работу... 🚀"
        )
        
        await message.reply_text(
            confirmation_message,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(
            f"Failed to process voice message: job_id={job_id}, "
            f"user_id={user.id}, error={str(e)}",
            exc_info=True
        )
        
        await message.reply_text(
            "❌ Произошла ошибка при обработке голосового сообщения. "
            "Пожалуйста, попробуйте еще раз."
        )


async def handle_callback_query(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle callback queries from inline keyboard buttons.
    
    Processes approval/cancellation actions for script, images, and videos.
    Callback data format: "approve_script:{job_id}" or "cancel_script:{job_id}"
    
    Supported callback types:
    - approve_script / cancel_script
    - approve_images / cancel_images
    - approve_videos / cancel_videos
    
    Args:
        update: Telegram update object
        context: Callback context
    """
    query = update.callback_query
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Answer callback query to remove loading state
    await query.answer()
    
    callback_data = query.data
    
    logger.info(
        f"Callback query received: user_id={user.id}, "
        f"chat_id={chat_id}, data={callback_data}"
    )
    
    # Parse callback data
    try:
        action, job_id = _parse_callback_data(callback_data)
    except ValueError as e:
        logger.error(f"Invalid callback data: {callback_data}, error={str(e)}")
        await query.edit_message_text(
            "❌ Ошибка: неверный формат данных. Пожалуйста, начните новую задачу."
        )
        return
    
    # Determine approval type from action
    approval_type = _get_approval_type(action)
    
    if not approval_type:
        logger.error(f"Unknown action in callback: {action}")
        await query.edit_message_text(
            "❌ Ошибка: неизвестное действие. Пожалуйста, начните новую задачу."
        )
        return
    
    # Process approval or cancellation
    if action.startswith("approve_"):
        await _handle_approval(query, job_id, approval_type, action)
    elif action.startswith("cancel_"):
        await _handle_cancellation(query, job_id, approval_type, action)
    else:
        logger.error(f"Unknown action type: {action}")
        await query.edit_message_text(
            "❌ Ошибка: неизвестный тип действия."
        )


def _parse_callback_data(callback_data: str) -> tuple[str, str]:
    """
    Parse callback data into action and job_id.
    
    Args:
        callback_data: String in format "action:job_id"
        
    Returns:
        Tuple of (action, job_id)
        
    Raises:
        ValueError: If callback data format is invalid
    """
    parts = callback_data.split(":", 1)
    
    if len(parts) != 2:
        raise ValueError(f"Invalid callback data format: {callback_data}")
    
    action, job_id = parts
    
    if not action or not job_id:
        raise ValueError(f"Empty action or job_id in callback data: {callback_data}")
    
    return action, job_id


def _get_approval_type(action: str) -> Optional[str]:
    """
    Extract approval type from action string.
    
    Args:
        action: Action string like "approve_script" or "cancel_images"
        
    Returns:
        Approval type ('script', 'images', 'videos') or None if unknown
    """
    if "script" in action:
        return "script"
    elif "images" in action:
        return "images"
    elif "videos" in action:
        return "videos"
    else:
        return None


async def _handle_approval(
    query,
    job_id: str,
    approval_type: str,
    action: str
) -> None:
    """
    Handle approval action.
    
    Args:
        query: Callback query object
        job_id: Job identifier
        approval_type: Type of approval ('script', 'images', 'videos')
        action: Original action string
    """
    logger.info(
        f"Processing approval: job_id={job_id}, type={approval_type}, action={action}"
    )
    
    try:
        # Set approval in Redis
        approval_manager.approve(job_id, approval_type)
        
        # Update message to show approval
        approval_messages = {
            "script": "✅ Сценарий утвержден!\n\nПродолжаю генерацию изображений... 🎨",
            "images": "✅ Изображения утверждены!\n\nНачинаю анимацию видео... 🎬",
            "videos": "✅ Видео утверждены!\n\nГенерирую озвучку и собираю финальное видео... 🎵"
        }
        
        message = approval_messages.get(
            approval_type,
            f"✅ {approval_type.capitalize()} утверждено!"
        )
        
        await query.edit_message_text(message)
        
        logger.info(
            f"Approval processed successfully: job_id={job_id}, type={approval_type}"
        )
        
    except Exception as e:
        logger.error(
            f"Failed to process approval: job_id={job_id}, "
            f"type={approval_type}, error={str(e)}",
            exc_info=True
        )
        
        await query.edit_message_text(
            "❌ Произошла ошибка при обработке утверждения. "
            "Пожалуйста, попробуйте еще раз."
        )


async def _handle_cancellation(
    query,
    job_id: str,
    approval_type: str,
    action: str
) -> None:
    """
    Handle cancellation action.
    
    Args:
        query: Callback query object
        job_id: Job identifier
        approval_type: Type of approval ('script', 'images', 'videos')
        action: Original action string
    """
    logger.info(
        f"Processing cancellation: job_id={job_id}, type={approval_type}, action={action}"
    )
    
    try:
        # Set cancellation in Redis
        approval_manager.cancel(job_id, approval_type)
        
        # Update message to show cancellation
        cancellation_messages = {
            "script": "❌ Задача отменена.\n\nСценарий не был утвержден. Временные файлы удалены.",
            "images": "❌ Задача отменена.\n\nИзображения не были утверждены. Временные файлы удалены.",
            "videos": "❌ Задача отменена.\n\nВидео не были утверждены. Временные файлы удалены."
        }
        
        message = cancellation_messages.get(
            approval_type,
            f"❌ Задача отменена на этапе: {approval_type}"
        )
        
        message += "\n\nВы можете начать новую задачу, отправив новое описание."
        
        await query.edit_message_text(message)
        
        logger.info(
            f"Cancellation processed successfully: job_id={job_id}, type={approval_type}"
        )
        
    except Exception as e:
        logger.error(
            f"Failed to process cancellation: job_id={job_id}, "
            f"type={approval_type}, error={str(e)}",
            exc_info=True
        )
        
        await query.edit_message_text(
            "❌ Произошла ошибка при обработке отмены. "
            "Задача будет автоматически отменена по истечении времени ожидания."
        )
