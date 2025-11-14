"""
Enhanced Telegram Bot Handlers with persistent keyboard buttons.

Provides persistent buttons: /start, /status, Подтвердить, Отклонить
"""

import logging
import uuid
from typing import Optional

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from app.config import Config
from app.services.approval_service import ApprovalManager
from app.tasks.video_generation_enhanced import generate_video_enhanced_task
from app.models.database import get_db_session
from app.models.video_job_enhanced import VideoJobEnhanced, VideoSegmentEnhanced


logger = logging.getLogger(__name__)

# Initialize approval manager
approval_manager = ApprovalManager()

# Persistent keyboard layout
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📊 Статус"), KeyboardButton("🔄 Старт")],
        [KeyboardButton("✅ Подтвердить"), KeyboardButton("❌ Отклонить")]
    ],
    resize_keyboard=True,
    persistent=True
)


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command and "🔄 Старт" button.
    Shows welcome message with persistent keyboard.
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(
        f"User started bot: user_id={user.id}, username={user.username}, chat_id={chat_id}"
    )
    
    welcome_message = (
        f"👋 Привет, {user.first_name}!\n\n"
        "🎬 Я бот для автоматической генерации рекламных видеороликов.\n\n"
        "📝 **Как использовать:**\n"
        "• Отправьте текстовое описание вашего ролика\n"
        "• Я создам профессиональное 50-секундное видео\n\n"
        "🎯 **Этапы генерации:**\n"
        "1️⃣ Сценарий (утверждение)\n"
        "2️⃣ Генерация промптов для изображений\n"
        "3️⃣ Создание 10 изображений (утверждение)\n"
        "4️⃣ Генерация промптов для анимации\n"
        "5️⃣ Анимация 10 видео (утверждение)\n"
        "6️⃣ Озвучка и финальная сборка\n\n"
        "⏱️ Время генерации: ~15-20 минут\n\n"
        "🎛️ **Кнопки управления:**\n"
        "• 📊 Статус — текущий статус задачи\n"
        "• ✅ Подтвердить — утвердить текущий этап\n"
        "• ❌ Отклонить — отменить задачу\n"
        "• 🔄 Старт — показать это сообщение\n\n"
        "Готовы начать? Отправьте описание вашего ролика!"
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=MAIN_KEYBOARD,
        parse_mode='Markdown'
    )


async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /status command and "📊 Статус" button.
    Shows current job status from database.
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"Status requested: user_id={user.id}, chat_id={chat_id}")
    
    db = get_db_session()
    try:
        # Get latest job for this user
        job = db.query(VideoJobEnhanced).filter_by(
            user_id=user.id
        ).order_by(
            VideoJobEnhanced.created_at.desc()
        ).first()
        
        if not job:
            await update.message.reply_text(
                "ℹ️ У вас пока нет активных задач.\n\n"
                "Отправьте описание ролика, чтобы начать генерацию!",
                reply_markup=MAIN_KEYBOARD
            )
            return
        
        # Build status message
        status_message = _build_status_message(job, db)
        
        await update.message.reply_text(
            status_message,
            reply_markup=MAIN_KEYBOARD,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Failed to get status: user_id={user.id}, error={str(e)}", exc_info=True)
        await update.message.reply_text(
            "❌ Ошибка при получении статуса. Попробуйте позже.",
            reply_markup=MAIN_KEYBOARD
        )
    finally:
        db.close()


async def handle_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle "✅ Подтвердить" button.
    Approves current stage of the latest job.
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"Approve requested: user_id={user.id}, chat_id={chat_id}")
    
    db = get_db_session()
    try:
        # Get latest job for this user
        job = db.query(VideoJobEnhanced).filter_by(
            user_id=user.id
        ).order_by(
            VideoJobEnhanced.created_at.desc()
        ).first()
        
        if not job:
            await update.message.reply_text(
                "ℹ️ Нет активных задач для утверждения.",
                reply_markup=MAIN_KEYBOARD
            )
            return
        
        # Determine what to approve based on status
        approval_type = _get_approval_type_from_status(job.status)
        
        if not approval_type:
            await update.message.reply_text(
                f"ℹ️ Текущий этап не требует утверждения.\n\n"
                f"Статус: {_translate_status(job.status)}",
                reply_markup=MAIN_KEYBOARD
            )
            return
        
        # Set approval
        approval_manager.approve(job.id, approval_type)
        
        approval_messages = {
            "script": "✅ Сценарий утверждён!\n\nНачинаю генерацию промптов для изображений...",
            "images": "✅ Изображения утверждены!\n\nНачинаю генерацию промптов для анимации...",
            "videos": "✅ Видео утверждены!\n\nГенерирую озвучку и собираю финальное видео..."
        }
        
        message = approval_messages.get(approval_type, "✅ Утверждено!")
        
        await update.message.reply_text(message, reply_markup=MAIN_KEYBOARD)
        
        logger.info(f"Approved: job_id={job.id}, type={approval_type}")
        
    except Exception as e:
        logger.error(f"Failed to approve: user_id={user.id}, error={str(e)}", exc_info=True)
        await update.message.reply_text(
            "❌ Ошибка при утверждении. Попробуйте позже.",
            reply_markup=MAIN_KEYBOARD
        )
    finally:
        db.close()


async def handle_reject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle "❌ Отклонить" button.
    Cancels current job and cleans up database.
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"Reject requested: user_id={user.id}, chat_id={chat_id}")
    
    db = get_db_session()
    try:
        # Get latest job for this user
        job = db.query(VideoJobEnhanced).filter_by(
            user_id=user.id
        ).order_by(
            VideoJobEnhanced.created_at.desc()
        ).first()
        
        if not job:
            await update.message.reply_text(
                "ℹ️ Нет активных задач для отмены.",
                reply_markup=MAIN_KEYBOARD
            )
            return
        
        if job.status in ['completed', 'cancelled', 'failed']:
            await update.message.reply_text(
                f"ℹ️ Задача уже завершена.\n\n"
                f"Статус: {_translate_status(job.status)}",
                reply_markup=MAIN_KEYBOARD
            )
            return
        
        # Determine approval type for cancellation
        approval_type = _get_approval_type_from_status(job.status)
        
        if approval_type:
            approval_manager.cancel(job.id, approval_type)
        
        # Update job status
        job.status = 'cancelled'
        db.commit()
        
        # Delete all segments
        db.query(VideoSegmentEnhanced).filter_by(job_id=job.id).delete()
        db.commit()
        
        await update.message.reply_text(
            "❌ Задача отменена.\n\n"
            "База данных очищена. Временные файлы будут удалены.\n\n"
            "Вы можете начать новую задачу, отправив описание ролика.",
            reply_markup=MAIN_KEYBOARD
        )
        
        logger.info(f"Rejected: job_id={job.id}")
        
    except Exception as e:
        logger.error(f"Failed to reject: user_id={user.id}, error={str(e)}", exc_info=True)
        await update.message.reply_text(
            "❌ Ошибка при отмене. Попробуйте позже.",
            reply_markup=MAIN_KEYBOARD
        )
    finally:
        db.close()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle text messages from users.
    Starts new video generation job.
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    message = update.message
    
    # Check for button commands
    text = message.text.strip()
    
    if text in ["🔄 Старт", "/start"]:
        await handle_start(update, context)
        return
    elif text in ["📊 Статус", "/status"]:
        await handle_status(update, context)
        return
    elif text == "✅ Подтвердить":
        await handle_approve(update, context)
        return
    elif text == "❌ Отклонить":
        await handle_reject(update, context)
        return
    
    # Regular message - start video generation
    prompt = text
    
    if not prompt:
        await message.reply_text(
            "❌ Описание не может быть пустым.",
            reply_markup=MAIN_KEYBOARD
        )
        return
    
    logger.info(
        f"Text message received: user_id={user.id}, chat_id={chat_id}, "
        f"prompt_length={len(prompt)}"
    )
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    try:
        # Start enhanced video generation task
        generate_video_enhanced_task.delay(
            job_id=job_id,
            user_id=user.id,
            chat_id=chat_id,
            prompt=prompt
        )
        
        logger.info(
            f"Enhanced video generation task started: job_id={job_id}, "
            f"user_id={user.id}, chat_id={chat_id}"
        )
        
        confirmation_message = (
            "✅ Ваш запрос принят!\n\n"
            f"🆔 ID задачи: `{job_id}`\n\n"
            "⏱️ Примерное время: 15-20 минут\n\n"
            "📊 Используйте кнопку **Статус** для отслеживания прогресса.\n"
            "✅ Кнопка **Подтвердить** для утверждения этапов.\n"
            "❌ Кнопка **Отклонить** для отмены задачи.\n\n"
            "Начинаю работу... 🚀"
        )
        
        await message.reply_text(
            confirmation_message,
            reply_markup=MAIN_KEYBOARD,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(
            f"Failed to start task: job_id={job_id}, error={str(e)}",
            exc_info=True
        )
        
        await message.reply_text(
            "❌ Ошибка при запуске задачи. Попробуйте позже.",
            reply_markup=MAIN_KEYBOARD
        )


def _build_status_message(job: VideoJobEnhanced, db) -> str:
    """Build detailed status message for a job."""
    
    status_emoji = {
        'pending': '⏳',
        'processing': '⚙️',
        'awaiting_script_approval': '📝',
        'script_approved': '✅',
        'images_approved': '✅',
        'videos_approved': '✅',
        'completed': '✅',
        'cancelled': '❌',
        'failed': '❌'
    }
    
    emoji = status_emoji.get(job.status, '❓')
    status_text = _translate_status(job.status)
    
    message = f"{emoji} **Статус задачи**\n\n"
    message += f"🆔 ID: `{job.id}`\n"
    message += f"📊 Статус: {status_text}\n"
    message += f"📝 Описание: {job.prompt[:100]}...\n\n"
    
    # Script stage
    if job.script_text:
        message += "✅ Сценарий: сгенерирован\n"
        if job.script_approved == 1:
            message += "   └─ Утверждён ✅\n"
        elif job.script_approved == -1:
            message += "   └─ Отклонён ❌\n"
        else:
            message += "   └─ Ожидает утверждения ⏳\n"
    else:
        message += "⏳ Сценарий: в процессе...\n"
    
    # Segments stage
    segments = db.query(VideoSegmentEnhanced).filter_by(job_id=job.id).all()
    
    if segments:
        message += f"\n📊 **Сегменты (10 шт.):**\n"
        
        # Count by status
        image_prompts_ready = sum(1 for s in segments if s.image_prompt)
        images_ready = sum(1 for s in segments if s.image_path)
        animation_prompts_ready = sum(1 for s in segments if s.animation_prompt)
        videos_ready = sum(1 for s in segments if s.video_path)
        
        message += f"• Промпты для изображений: {image_prompts_ready}/10\n"
        message += f"• Изображения: {images_ready}/10\n"
        message += f"• Промпты для анимации: {animation_prompts_ready}/10\n"
        message += f"• Видео: {videos_ready}/10\n"
    
    # Audio stage
    if job.audio_path:
        message += f"\n✅ Озвучка: готова ({job.audio_duration:.1f}с)\n"
    
    # Final video
    if job.final_video_path:
        message += f"\n✅ Финальное видео: готово\n"
        message += f"   └─ Размер: {job.final_video_size_mb:.1f} МБ\n"
        message += f"   └─ Длительность: {job.final_video_duration:.1f}с\n"
    
    # Timestamps
    if job.created_at:
        message += f"\n🕐 Создано: {job.created_at.strftime('%H:%M:%S')}\n"
    if job.completed_at:
        message += f"✅ Завершено: {job.completed_at.strftime('%H:%M:%S')}\n"
    
    return message


def _translate_status(status: str) -> str:
    """Translate status to Russian."""
    translations = {
        'pending': 'Ожидание',
        'processing': 'Обработка',
        'awaiting_script_approval': 'Ожидание утверждения сценария',
        'script_approved': 'Сценарий утверждён',
        'images_approved': 'Изображения утверждены',
        'videos_approved': 'Видео утверждены',
        'completed': 'Завершено',
        'cancelled': 'Отменено',
        'failed': 'Ошибка'
    }
    return translations.get(status, status)


def _get_approval_type_from_status(status: str) -> Optional[str]:
    """Determine what needs approval based on job status."""
    if status == 'awaiting_script_approval':
        return 'script'
    elif 'images' in status.lower() and 'approval' in status.lower():
        return 'images'
    elif 'videos' in status.lower() and 'approval' in status.lower():
        return 'videos'
    return None
