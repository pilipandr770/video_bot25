# Voice Message Handling Implementation

## Overview
Implemented voice message handling in the video generation task (Task 26) to support transcription of voice messages before video generation.

## Changes Made

### 1. Modified `app/tasks/video_generation.py`

#### Added Imports
- `from telegram import Bot`
- `from telegram.error import TelegramError`

#### Added Voice Message Processing Stage (Stage 0)
- Detects special marker `__VOICE_MESSAGE__|{file_id}` in the prompt
- Downloads voice file from Telegram using the file_id
- Transcribes audio using OpenAI Whisper API
- Sends transcribed text back to user for confirmation
- Uses transcribed text as the actual prompt for script generation

#### Added Helper Function: `_transcribe_voice_message()`
```python
def _transcribe_voice_message(
    prompt: str,
    openai_service: OpenAIService,
    job_id: str,
    chat_id: int
) -> str
```

**Functionality:**
- Validates voice message marker format
- Extracts file_id from marker
- Downloads voice file from Telegram using Bot API
- Transcribes audio using OpenAI Whisper
- Returns transcribed text
- Handles errors with proper logging and user-friendly messages

**Error Handling:**
- `TelegramError`: Failed to download voice file
- `OpenAIServiceError`: Failed to transcribe audio
- `ValueError`: Invalid marker format or empty transcription
- Generic exceptions with detailed logging

### 2. Modified `app/bot/notifications.py`

#### Added Method: `send_message()`
```python
async def send_message(
    self,
    chat_id: int,
    text: str,
    job_id: Optional[str] = None,
    parse_mode: Optional[str] = None
) -> None
```

**Purpose:** Send generic text messages to users (used for transcription confirmation)

#### Enhanced Method: `send_status_update()`
- Added `custom_message` parameter to override default status messages
- Used for sending custom status like "🎤 Распознаю голосовое сообщение..."

### 3. Voice Message Flow in `app/bot/handlers.py`

The handler already creates the special marker when a voice message is received:
```python
prompt = f"__VOICE_MESSAGE__|{voice.file_id}"
```

This marker is now properly handled in the video generation task.

## Complete Flow

1. **User sends voice message** → `handle_voice()` in handlers.py
2. **Handler creates marker** → `__VOICE_MESSAGE__|{file_id}`
3. **Task starts** → `generate_video_task()` receives marker
4. **Stage 0: Transcription**
   - Detects marker
   - Downloads voice file from Telegram
   - Transcribes using OpenAI Whisper
   - Sends transcribed text to user
5. **Stage 1+: Normal flow** → Uses transcribed text as prompt

## Error Messages

Added to `ERROR_MESSAGES` in notifications.py:
- `transcription_error`: User-friendly message for transcription failures

## Testing

Created `test_voice_message_handling.py` with tests for:
- Voice message marker detection
- File ID extraction from markers
- Edge cases (empty prompts, invalid formats)

All tests pass successfully.

## Requirements Satisfied

✅ **2.1**: Voice message acceptance and confirmation  
✅ **2.2**: Voice message validation  
✅ **2.3**: Voice file download from Telegram API  
✅ **2.4**: Transcription using OpenAI Whisper  
✅ **2.5**: Using transcribed text for video generation  

## Logging

Added structured logging for:
- `voice_download_started`
- `voice_download_completed`
- `voice_transcription_started`
- `voice_transcription_completed`
- `telegram_download_failed`
- `openai_transcription_failed`
- `voice_processing_failed`

## Metrics

Voice transcription stage metrics include:
- Duration in seconds
- Transcribed text length
- Word count

## Notes

- Voice messages are processed synchronously before script generation
- User receives confirmation of transcribed text before video generation begins
- All temporary voice files are handled in memory (no disk storage needed)
- Proper error handling ensures user gets clear feedback if transcription fails
