"""
Test bot in polling mode (without webhook).
This script runs the bot locally and polls Telegram for updates.
"""
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load environment variables
load_dotenv()

import os

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я AI Video Generator Bot.\n\n"
        "🎬 Отправь мне текст, и я создам для тебя видео!\n\n"
        "Доступные команды:\n"
        "/start - начать работу\n"
        "/help - помощь\n"
        "/status - проверить статус"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "📖 Помощь:\n\n"
        "1. Отправь мне текст для видео\n"
        "2. Я создам сценарий и сгенерирую видео\n"
        "3. Ты получишь готовое видео\n\n"
        "Команды:\n"
        "/start - начать\n"
        "/help - эта справка\n"
        "/status - статус системы"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    await update.message.reply_text(
        "✅ Бот работает!\n\n"
        "Режим: Polling (тестовый)\n"
        "Статус: Онлайн"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    user_message = update.message.text
    user = update.effective_user
    
    logger.info(f"Received message from {user.username}: {user_message}")
    
    await update.message.reply_text(
        f"📝 Получил твое сообщение:\n\n"
        f'"{user_message}"\n\n'
        "⚠️ Это тестовый режим. Генерация видео пока не работает.\n"
        "Для полноценной работы нужно настроить webhook или деплой."
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")


def main():
    """Start the bot in polling mode"""
    print("🚀 Starting bot in polling mode...")
    print(f"📱 Bot token: {BOT_TOKEN[:10]}...")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start polling
    print("✅ Bot is running! Press Ctrl+C to stop.")
    print("📨 Send /start to your bot in Telegram to test")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
