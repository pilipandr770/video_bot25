"""
Validators for AI Video Generator Bot.

This module provides validation functions for incoming Telegram messages
to ensure they meet the requirements before processing.
"""

import logging
from typing import Optional

from telegram import Message


logger = logging.getLogger(__name__)


# Constants
MAX_VOICE_SIZE_MB = 20
MAX_VOICE_SIZE_BYTES = MAX_VOICE_SIZE_MB * 1024 * 1024


def validate_message(message: Message) -> bool:
    """
    Validate that the message is of an acceptable type (text or voice).
    
    According to requirements 1.2 and 2.2, the system should accept
    text messages and voice messages for video generation.
    
    Args:
        message: Telegram Message object to validate
        
    Returns:
        True if message is valid (text or voice), False otherwise
        
    Examples:
        >>> # Text message
        >>> validate_message(text_message)
        True
        
        >>> # Voice message
        >>> validate_message(voice_message)
        True
        
        >>> # Photo message (invalid)
        >>> validate_message(photo_message)
        False
    """
    if message is None:
        logger.warning("Validation failed: message is None")
        return False
    
    # Check if message has text content
    has_text = message.text is not None and len(message.text.strip()) > 0
    
    # Check if message has voice content
    has_voice = message.voice is not None
    
    # Message is valid if it has either text or voice
    is_valid = has_text or has_voice
    
    if not is_valid:
        logger.warning(
            f"Validation failed: message has neither text nor voice. "
            f"message_id={message.message_id}"
        )
    
    return is_valid


def validate_voice_size(message: Message) -> tuple[bool, Optional[str]]:
    """
    Validate that a voice message does not exceed the maximum size limit.
    
    According to requirement 2.2, voice messages must be validated for size.
    The maximum allowed size is 20 MB to ensure reasonable processing times
    and prevent resource exhaustion.
    
    Args:
        message: Telegram Message object containing a voice message
        
    Returns:
        Tuple of (is_valid, error_message):
        - is_valid: True if voice size is acceptable, False otherwise
        - error_message: Human-readable error message if invalid, None if valid
        
    Examples:
        >>> # Valid voice message (5 MB)
        >>> is_valid, error = validate_voice_size(small_voice_message)
        >>> assert is_valid == True
        >>> assert error is None
        
        >>> # Invalid voice message (25 MB)
        >>> is_valid, error = validate_voice_size(large_voice_message)
        >>> assert is_valid == False
        >>> assert "20 МБ" in error
    """
    if message is None:
        error_msg = "Message is None"
        logger.warning(f"Voice size validation failed: {error_msg}")
        return False, error_msg
    
    # Check if message has voice
    if message.voice is None:
        error_msg = "Message does not contain a voice message"
        logger.warning(
            f"Voice size validation failed: {error_msg}. "
            f"message_id={message.message_id}"
        )
        return False, error_msg
    
    voice = message.voice
    file_size = voice.file_size
    
    # Validate size
    if file_size > MAX_VOICE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        error_msg = (
            f"Голосовое сообщение слишком большое ({size_mb:.1f} МБ). "
            f"Максимальный размер: {MAX_VOICE_SIZE_MB} МБ. "
            "Пожалуйста, отправьте более короткое сообщение или используйте текст."
        )
        
        logger.warning(
            f"Voice size validation failed: size={size_mb:.2f} MB exceeds "
            f"limit of {MAX_VOICE_SIZE_MB} MB. message_id={message.message_id}"
        )
        
        return False, error_msg
    
    # Voice size is valid
    size_kb = file_size / 1024
    logger.debug(
        f"Voice size validation passed: size={size_kb:.2f} KB, "
        f"duration={voice.duration}s, message_id={message.message_id}"
    )
    
    return True, None


def validate_text_message(message: Message) -> tuple[bool, Optional[str]]:
    """
    Validate that a text message is not empty.
    
    Helper function to ensure text messages contain actual content
    before processing.
    
    Args:
        message: Telegram Message object containing a text message
        
    Returns:
        Tuple of (is_valid, error_message):
        - is_valid: True if text is not empty, False otherwise
        - error_message: Human-readable error message if invalid, None if valid
    """
    if message is None:
        error_msg = "Message is None"
        logger.warning(f"Text validation failed: {error_msg}")
        return False, error_msg
    
    # Check if message has text
    if message.text is None:
        error_msg = "Message does not contain text"
        logger.warning(
            f"Text validation failed: {error_msg}. "
            f"message_id={message.message_id}"
        )
        return False, error_msg
    
    # Check if text is not empty after stripping whitespace
    text = message.text.strip()
    if not text:
        error_msg = (
            "Описание не может быть пустым. "
            "Пожалуйста, опишите ваш рекламный ролик."
        )
        logger.warning(
            f"Text validation failed: empty text. "
            f"message_id={message.message_id}"
        )
        return False, error_msg
    
    logger.debug(
        f"Text validation passed: length={len(text)} chars, "
        f"message_id={message.message_id}"
    )
    
    return True, None
