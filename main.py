"""
Main entry point for AI Video Generator Bot Flask application.
"""
import logging
import logging.config
import structlog
import signal
import sys
import asyncio
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

from app.config import Config
from app.bot.webhook import register_webhook_blueprint, set_webhook, delete_webhook, get_telegram_application

# Load environment variables from .env file
load_dotenv()

# Global flag for graceful shutdown
shutdown_flag = False


def configure_logging():
    """
    Configure structured logging with structlog.
    
    Sets up logging with appropriate processors for both development and production:
    - Development: Human-readable console output with colors
    - Production: JSON formatted logs for log aggregation systems
    
    Requirements: 10.1, 11.5
    """
    # Determine if we're in development mode
    is_development = Config.LOG_LEVEL == "DEBUG"
    
    # Configure standard library logging
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "plain": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(colors=is_development),
            },
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
            },
        },
        "handlers": {
            "default": {
                "level": Config.LOG_LEVEL,
                "class": "logging.StreamHandler",
                "formatter": "plain" if is_development else "json",
            },
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": Config.LOG_LEVEL,
                "propagate": True,
            },
        }
    })
    
    # Configure structlog processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if is_development:
        # Development: human-readable output with colors
        processors = shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ]
    else:
        # Production: JSON output for log aggregation
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ]
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


# Configure logging before creating the app
configure_logging()

# Create Flask application
app = Flask(__name__)
app.config.from_object(Config)


def get_user_id_from_request():
    """
    Extract user ID from Telegram webhook request for rate limiting.
    
    Returns:
        User ID as string, or remote address if user ID not found
    """
    try:
        data = request.get_json(force=True, silent=True)
        if data:
            # Try to get user ID from message
            if "message" in data:
                user_id = data["message"].get("from", {}).get("id")
                if user_id:
                    return str(user_id)
            
            # Try to get user ID from callback query
            if "callback_query" in data:
                user_id = data["callback_query"].get("from", {}).get("id")
                if user_id:
                    return str(user_id)
        
        # Fallback to IP address
        return get_remote_address()
        
    except Exception:
        # Fallback to IP address on any error
        return get_remote_address()


# Configure rate limiter with in-memory storage
# Note: In-memory storage is suitable for single-instance deployments
# For multi-instance deployments, consider using Redis or another shared storage
limiter = Limiter(
    app=app,
    key_func=get_user_id_from_request,
    default_limits=[],  # No default limits, we'll apply them per route
    storage_uri="memory://",
    strategy="fixed-window"
)

# Register webhook blueprint with rate limiting
register_webhook_blueprint(app, limiter)

# Setup logging
logging.basicConfig(
    format="%(message)s",
    level=getattr(logging, Config.LOG_LEVEL),
)
logger = structlog.get_logger()


# Initialize application (must be called at module level for gunicorn)
try:
    # Validate configuration
    Config.validate()
    logger.info("configuration_validated")
    
    # Ensure required directories exist
    Config.ensure_directories()
    logger.info("directories_initialized", temp_dir=Config.TEMP_DIR)
    
    # Set up Telegram webhook
    if Config.TELEGRAM_WEBHOOK_URL:
        try:
            # Run async webhook setup
            asyncio.run(setup_telegram_webhook())
        except Exception as e:
            logger.error(
                "failed_to_setup_webhook",
                error=str(e),
                exc_info=True
            )
            # Don't fail startup if webhook setup fails
    
    logger.info(
        "application_initialized",
        max_concurrent_jobs=Config.MAX_CONCURRENT_JOBS,
        target_video_duration=Config.TARGET_VIDEO_DURATION,
        num_segments=Config.NUM_SEGMENTS
    )
except ValueError as e:
    logger.error("configuration_error", error=str(e))
    raise


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Render.com."""
    return jsonify({
        "status": "healthy",
        "service": "ai-video-generator-bot"
    }), 200


@app.route("/", methods=["GET"])
def index():
    """Root endpoint."""
    return jsonify({
        "service": "AI Video Generator Bot",
        "status": "running"
    }), 200


@app.before_request
def log_request():
    """Log incoming requests."""
    logger.info(
        "incoming_request",
        method=request.method,
        path=request.path,
        remote_addr=request.remote_addr
    )


@app.errorhandler(429)
async def handle_rate_limit_exceeded(error):
    """
    Handle rate limit exceeded errors.
    
    Sends a user-friendly notification to the Telegram user when they
    exceed the rate limit (5 requests per minute, 20 per hour).
    """
    logger.warning(
        "rate_limit_exceeded",
        remote_addr=request.remote_addr,
        path=request.path
    )
    
    # Try to send notification to user
    try:
        data = request.get_json(force=True, silent=True)
        if data:
            chat_id = None
            
            # Extract chat_id from message or callback query
            if "message" in data:
                chat_id = data["message"].get("chat", {}).get("id")
            elif "callback_query" in data:
                chat_id = data["callback_query"].get("message", {}).get("chat", {}).get("id")
            
            # Send notification if we have chat_id
            if chat_id:
                from app.bot.notifications import NotificationService
                notification_service = NotificationService()
                
                rate_limit_message = (
                    "⏳ Вы отправляете запросы слишком часто.\n\n"
                    "Пожалуйста, подождите немного перед следующим запросом.\n\n"
                    "📊 Лимиты:\n"
                    f"• {Config.RATE_LIMIT_PER_MINUTE} запросов в минуту\n"
                    f"• {Config.RATE_LIMIT_PER_HOUR} запросов в час"
                )
                
                await notification_service.bot.send_message(
                    chat_id=chat_id,
                    text=rate_limit_message
                )
                
                logger.info(
                    "rate_limit_notification_sent",
                    chat_id=chat_id
                )
    
    except Exception as e:
        logger.error(
            "failed_to_send_rate_limit_notification",
            error=str(e),
            exc_info=True
        )
    
    # Return standard rate limit response
    return jsonify({
        "error": "Rate limit exceeded",
        "message": "Too many requests. Please try again later."
    }), 429


@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler."""
    logger.error(
        "unhandled_exception",
        error=str(error),
        error_type=type(error).__name__
    )
    return jsonify({
        "error": "Internal server error"
    }), 500


async def setup_telegram_webhook():
    """
    Set up Telegram webhook.
    
    Configures Telegram to send updates to the webhook endpoint.
    This should be called during application startup.
    
    Requirements: 11.1
    """
    # Initialize Telegram application first
    from app.bot.webhook import initialize_telegram_application
    await initialize_telegram_application()
    logger.info("telegram_application_initialized")
    
    if not Config.TELEGRAM_WEBHOOK_URL:
        logger.warning(
            "telegram_webhook_url_not_configured",
            message="TELEGRAM_WEBHOOK_URL not set. Webhook will not be configured."
        )
        return False
    
    try:
        webhook_url = f"{Config.TELEGRAM_WEBHOOK_URL}/webhook"
        
        logger.info(
            "setting_telegram_webhook",
            webhook_url=webhook_url
        )
        
        # Set webhook with optional secret token
        secret_token = getattr(Config, 'TELEGRAM_WEBHOOK_SECRET', None)
        success = await set_webhook(webhook_url, secret_token)
        
        if success:
            logger.info(
                "telegram_webhook_configured",
                webhook_url=webhook_url
            )
        else:
            logger.error(
                "failed_to_configure_telegram_webhook",
                webhook_url=webhook_url
            )
        
        return success
        
    except Exception as e:
        logger.error(
            "error_configuring_telegram_webhook",
            error=str(e),
            exc_info=True
        )
        return False


async def cleanup_resources():
    """
    Clean up resources during graceful shutdown.
    
    This function is called when the application is shutting down to:
    - Delete the Telegram webhook
    - Clean up any temporary files
    - Close connections
    
    Requirements: 11.1
    """
    global shutdown_flag
    shutdown_flag = True
    
    logger.info("starting_graceful_shutdown")
    
    try:
        # Delete Telegram webhook
        logger.info("deleting_telegram_webhook")
        await delete_webhook()
        logger.info("telegram_webhook_deleted")
        
    except Exception as e:
        logger.error(
            "error_during_webhook_cleanup",
            error=str(e),
            exc_info=True
        )
    
    try:
        # Clean up temporary files
        from app.utils.file_manager import FileManager
        
        logger.info("cleaning_up_temporary_files")
        file_manager = FileManager()
        file_manager.cleanup_old_files(max_age_hours=0)  # Clean all files
        logger.info("temporary_files_cleaned")
        
    except Exception as e:
        logger.error(
            "error_during_file_cleanup",
            error=str(e),
            exc_info=True
        )
    
    try:
        # Shutdown Telegram application
        telegram_app = get_telegram_application()
        if telegram_app:
            logger.info("shutting_down_telegram_application")
            await telegram_app.shutdown()
            logger.info("telegram_application_shutdown")
        
    except Exception as e:
        logger.error(
            "error_during_telegram_shutdown",
            error=str(e),
            exc_info=True
        )
    
    logger.info("graceful_shutdown_completed")


def signal_handler(signum, frame):
    """
    Handle shutdown signals (SIGTERM, SIGINT).
    
    This handler is called when the application receives a shutdown signal
    (e.g., Ctrl+C or container stop). It triggers graceful shutdown.
    
    Requirements: 11.1
    """
    signal_name = signal.Signals(signum).name
    logger.info(
        "shutdown_signal_received",
        signal=signal_name
    )
    
    # Run cleanup in async context
    try:
        asyncio.run(cleanup_resources())
    except Exception as e:
        logger.error(
            "error_during_signal_handler_cleanup",
            error=str(e),
            exc_info=True
        )
    
    # Exit gracefully
    sys.exit(0)


# Register signal handlers for graceful shutdown
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


if __name__ == "__main__":
    try:
        logger.info(
            "starting_flask_server",
            host="0.0.0.0",
            port=5000,
            debug=Config.LOG_LEVEL == "DEBUG"
        )
        
        # Run Flask development server
        app.run(
            host="0.0.0.0",
            port=5000,
            debug=Config.LOG_LEVEL == "DEBUG"
        )
        
    except KeyboardInterrupt:
        logger.info("keyboard_interrupt_received")
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        logger.error(
            "application_startup_failed",
            error=str(e),
            exc_info=True
        )
        sys.exit(1)
