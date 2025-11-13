"""
Telegram Webhook Handler for AI Video Generator Bot.

This module provides Flask endpoints for receiving and processing
Telegram webhook updates. It validates incoming requests and routes
them to appropriate handlers.
"""

import logging
import hmac
import hashlib
from typing import Optional

from flask import Blueprint, request, jsonify
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from app.config import Config
from app.bot.handlers import (
    handle_start,
    handle_message,
    handle_voice,
    handle_callback_query
)


logger = logging.getLogger(__name__)

# Create Blueprint for webhook routes
webhook_bp = Blueprint('webhook', __name__)

# Global application instance
telegram_app: Optional[Application] = None


def create_telegram_application() -> Application:
    """
    Create and configure Telegram Application with handlers.
    
    Returns:
        Configured Application instance
    """
    # Create application
    application = (
        Application.builder()
        .token(Config.TELEGRAM_BOT_TOKEN)
        .build()
    )
    
    # Register handlers
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    logger.info("Telegram application created and handlers registered")
    
    return application


async def initialize_telegram_application() -> Application:
    """
    Initialize Telegram Application instance.
    
    Returns:
        Initialized Application instance
    """
    global telegram_app
    
    if telegram_app is None:
        telegram_app = create_telegram_application()
        await telegram_app.initialize()
        logger.info("Telegram application initialized")
    
    return telegram_app


def get_telegram_application() -> Application:
    """
    Get Telegram Application instance.
    
    Returns:
        Application instance
    """
    global telegram_app
    
    if telegram_app is None:
        telegram_app = create_telegram_application()
    
    return telegram_app


def validate_telegram_request(request_data: bytes, token: str, headers: Optional[dict] = None) -> bool:
    """
    Validate that the request comes from Telegram.
    
    This is a basic validation. For production, you might want to implement
    additional security measures like checking the X-Telegram-Bot-Api-Secret-Token
    header if you set one when configuring the webhook.
    
    Args:
        request_data: Raw request body
        token: Telegram bot token
        headers: Optional request headers dict
        
    Returns:
        True if request appears valid, False otherwise
    """
    # Basic validation: check if request contains expected Telegram update structure
    try:
        if not request_data:
            return False
        
        # Additional validation can be added here
        # For example, checking X-Telegram-Bot-Api-Secret-Token header
        if headers:
            secret_token = headers.get('X-Telegram-Bot-Api-Secret-Token')
            expected_secret = Config.TELEGRAM_WEBHOOK_SECRET if hasattr(Config, 'TELEGRAM_WEBHOOK_SECRET') else None
            
            if expected_secret and secret_token != expected_secret:
                logger.warning("Invalid webhook secret token")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating Telegram request: {str(e)}")
        return False


@webhook_bp.route('/webhook', methods=['POST'])
async def webhook():
    """
    Main webhook endpoint for receiving Telegram updates.
    
    This endpoint receives POST requests from Telegram with update objects
    and processes them through the registered handlers.
    
    Rate limited to 5 requests per minute and 20 requests per hour per user.
    
    Returns:
        JSON response with status
    """
    try:
        # Get request data
        request_data = request.get_data()
        
        # Validate request
        if not validate_telegram_request(request_data, Config.TELEGRAM_BOT_TOKEN, dict(request.headers)):
            logger.warning(
                "Invalid webhook request",
                extra={
                    "remote_addr": request.remote_addr,
                    "content_length": len(request_data) if request_data else 0
                }
            )
            return jsonify({"error": "Invalid request"}), 403
        
        # Parse update
        update_data = request.get_json(force=True)
        
        if not update_data:
            logger.warning("Empty update data received")
            return jsonify({"error": "Empty update"}), 400
        
        logger.info(
            "Webhook update received",
            extra={
                "update_id": update_data.get("update_id"),
                "has_message": "message" in update_data,
                "has_callback_query": "callback_query" in update_data
            }
        )
        
        # Get or initialize application
        app = get_telegram_application()
        
        # Initialize if not already initialized
        if not app.running:
            await app.initialize()
            logger.info("Telegram application initialized in webhook handler")
        
        # Create Update object
        update = Update.de_json(update_data, app.bot)
        
        # Process update through application
        await app.process_update(update)
        
        logger.info(
            "Webhook update processed successfully",
            extra={"update_id": update.update_id}
        )
        
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(
            "Error processing webhook update",
            extra={
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        
        # Return 200 to prevent Telegram from retrying
        # Log the error for investigation
        return jsonify({"status": "error", "message": "Internal error"}), 200


@webhook_bp.route('/webhook', methods=['GET'])
def webhook_info():
    """
    GET endpoint for webhook information.
    
    Useful for debugging and verifying webhook is accessible.
    
    Returns:
        JSON with webhook information
    """
    return jsonify({
        "endpoint": "/webhook",
        "method": "POST",
        "status": "ready",
        "bot_configured": Config.TELEGRAM_BOT_TOKEN is not None
    }), 200


async def set_webhook(webhook_url: str, secret_token: Optional[str] = None) -> bool:
    """
    Set Telegram webhook URL.
    
    This should be called during application initialization to configure
    Telegram to send updates to the webhook endpoint.
    
    Args:
        webhook_url: Full URL where Telegram should send updates
        secret_token: Optional secret token for additional security
        
    Returns:
        True if webhook was set successfully, False otherwise
    """
    try:
        application = get_telegram_application()
        
        # Set webhook
        webhook_params = {
            "url": webhook_url,
            "allowed_updates": ["message", "callback_query"],
            "drop_pending_updates": True
        }
        
        if secret_token:
            webhook_params["secret_token"] = secret_token
        
        success = await application.bot.set_webhook(**webhook_params)
        
        if success:
            logger.info(
                "Webhook set successfully",
                extra={"webhook_url": webhook_url}
            )
        else:
            logger.error(
                "Failed to set webhook",
                extra={"webhook_url": webhook_url}
            )
        
        return success
        
    except Exception as e:
        logger.error(
            "Error setting webhook",
            extra={
                "webhook_url": webhook_url,
                "error": str(e)
            },
            exc_info=True
        )
        return False


async def delete_webhook() -> bool:
    """
    Delete Telegram webhook.
    
    Useful for switching back to polling mode or cleaning up.
    
    Returns:
        True if webhook was deleted successfully, False otherwise
    """
    try:
        application = get_telegram_application()
        success = await application.bot.delete_webhook(drop_pending_updates=True)
        
        if success:
            logger.info("Webhook deleted successfully")
        else:
            logger.error("Failed to delete webhook")
        
        return success
        
    except Exception as e:
        logger.error(
            "Error deleting webhook",
            extra={"error": str(e)},
            exc_info=True
        )
        return False


async def get_webhook_info() -> dict:
    """
    Get current webhook information from Telegram.
    
    Returns:
        Dictionary with webhook information
    """
    try:
        application = get_telegram_application()
        webhook_info = await application.bot.get_webhook_info()
        
        return {
            "url": webhook_info.url,
            "has_custom_certificate": webhook_info.has_custom_certificate,
            "pending_update_count": webhook_info.pending_update_count,
            "last_error_date": webhook_info.last_error_date,
            "last_error_message": webhook_info.last_error_message,
            "max_connections": webhook_info.max_connections,
            "allowed_updates": webhook_info.allowed_updates
        }
        
    except Exception as e:
        logger.error(
            "Error getting webhook info",
            extra={"error": str(e)},
            exc_info=True
        )
        return {"error": str(e)}


def register_webhook_blueprint(app, limiter=None):
    """
    Register webhook blueprint with Flask app.
    
    Args:
        app: Flask application instance
        limiter: Optional Flask-Limiter instance for rate limiting
    """
    app.register_blueprint(webhook_bp)
    
    # Apply rate limiting to webhook endpoint if limiter is provided
    if limiter:
        from app.config import Config
        rate_limit_string = f"{Config.RATE_LIMIT_PER_MINUTE}/minute;{Config.RATE_LIMIT_PER_HOUR}/hour"
        limiter.limit(rate_limit_string)(webhook)
        logger.info(
            "Webhook blueprint registered with rate limiting",
            extra={"rate_limit": rate_limit_string}
        )
    else:
        logger.info("Webhook blueprint registered")

