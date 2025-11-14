"""
OpenAI Service for AI Video Generator Bot.
Handles script generation, audio transcription, and text-to-speech.
"""
import time
import logging
import structlog
from typing import Optional
from pathlib import Path

from openai import OpenAI, APIError, RateLimitError, APITimeoutError
from openai.types.beta.threads import Run

from app.config import Config


logger = structlog.get_logger(__name__)


class OpenAIServiceError(Exception):
    """Base exception for OpenAI service errors."""
    pass


class OpenAIRateLimitError(OpenAIServiceError):
    """Exception raised when rate limit is exceeded."""
    pass


class OpenAIService:
    """Service for interacting with OpenAI API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI service.
        
        Args:
            api_key: OpenAI API key (defaults to Config.OPENAI_API_KEY)
        """
        self.api_key = api_key or Config.OPENAI_API_KEY
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Three specialized assistants
        self.script_assistant_id = Config.OPENAI_SCRIPT_ASSISTANT_ID
        self.segment_assistant_id = Config.OPENAI_SEGMENT_ASSISTANT_ID
        self.animation_assistant_id = Config.OPENAI_ANIMATION_ASSISTANT_ID
        
        if not self.script_assistant_id:
            raise ValueError("Script Assistant ID is required")
        if not self.segment_assistant_id:
            raise ValueError("Segment Assistant ID is required")
        if not self.animation_assistant_id:
            raise ValueError("Animation Assistant ID is required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.max_retries = Config.OPENAI_MAX_RETRIES
        
        logger.info(
            "openai_service_initialized",
            script_assistant_id=self.script_assistant_id,
            segment_assistant_id=self.segment_assistant_id,
            animation_assistant_id=self.animation_assistant_id,
            max_retries=self.max_retries
        )
    
    def generate_script(self, prompt: str) -> str:
        """
        Generate video script using Script Assistant.
        
        Args:
            prompt: User's description of the video topic
            
        Returns:
            Generated script text
            
        Raises:
            OpenAIServiceError: If script generation fails after retries
            OpenAIRateLimitError: If rate limit is exceeded
        """
        start_time = time.time()
        logger.info(
            "script_generation_started",
            prompt_length=len(prompt),
            prompt_preview=prompt[:100],
            assistant_id=self.script_assistant_id
        )
        
        script = self._call_assistant(
            assistant_id=self.script_assistant_id,
            user_message=prompt,
            operation_name="script generation"
        )
        
        duration = time.time() - start_time
        logger.info(
            "script_generation_completed",
            script_length=len(script),
            script_words=len(script.split()),
            duration_seconds=round(duration, 2)
        )
        
        return script
    
    def generate_image_prompt(self, segment_text: str) -> str:
        """
        Generate image prompt using Segment Assistant.
        
        Args:
            segment_text: Text content of the script segment
            
        Returns:
            Image generation prompt for Runway API
            
        Raises:
            OpenAIServiceError: If prompt generation fails after retries
            OpenAIRateLimitError: If rate limit is exceeded
        """
        start_time = time.time()
        logger.info(
            "image_prompt_generation_started",
            segment_text_length=len(segment_text),
            assistant_id=self.segment_assistant_id
        )
        
        prompt = self._call_assistant(
            assistant_id=self.segment_assistant_id,
            user_message=segment_text,
            operation_name="image prompt generation"
        )
        
        duration = time.time() - start_time
        logger.info(
            "image_prompt_generation_completed",
            prompt_length=len(prompt),
            duration_seconds=round(duration, 2)
        )
        
        return prompt.strip()
    
    def generate_animation_prompt(self, segment_text: str) -> str:
        """
        Generate animation prompt using Animation Assistant.
        
        Args:
            segment_text: Text content of the script segment
            
        Returns:
            Animation prompt for Runway API
            
        Raises:
            OpenAIServiceError: If prompt generation fails after retries
            OpenAIRateLimitError: If rate limit is exceeded
        """
        start_time = time.time()
        logger.info(
            "animation_prompt_generation_started",
            segment_text_length=len(segment_text),
            assistant_id=self.animation_assistant_id
        )
        
        prompt = self._call_assistant(
            assistant_id=self.animation_assistant_id,
            user_message=segment_text,
            operation_name="animation prompt generation"
        )
        
        duration = time.time() - start_time
        logger.info(
            "animation_prompt_generation_completed",
            prompt_length=len(prompt),
            duration_seconds=round(duration, 2)
        )
        
        return prompt.strip()
    
    def _call_assistant(self, assistant_id: str, user_message: str, operation_name: str) -> str:
        """
        Call OpenAI Assistant and get response.
        
        Args:
            assistant_id: ID of the assistant to use
            user_message: Message to send to the assistant
            operation_name: Name of the operation (for logging)
            
        Returns:
            Assistant's response text
            
        Raises:
            OpenAIServiceError: If assistant call fails
        """
        def _call():
            # Create a thread
            thread = self.client.beta.threads.create()
            
            # Add user message to thread
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_message
            )
            
            # Run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant_id
            )
            
            # Wait for completion
            while run.status in ["queued", "in_progress"]:
                time.sleep(1)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
            
            if run.status != "completed":
                raise OpenAIServiceError(
                    f"Assistant run failed with status: {run.status}"
                )
            
            # Retrieve messages
            messages = self.client.beta.threads.messages.list(
                thread_id=thread.id
            )
            
            # Get the assistant's response (first message from assistant)
            for message in messages.data:
                if message.role == "assistant":
                    # Extract text content
                    for content in message.content:
                        if content.type == "text":
                            return content.text.value
            
            raise OpenAIServiceError("No response from assistant")
        
        return self._retry_with_backoff(_call, operation_name)
    
    def transcribe_audio(self, audio_file: bytes, filename: str = "audio.ogg") -> str:
        """
        Transcribe audio file using OpenAI Whisper API.
        
        Args:
            audio_file: Audio file content as bytes
            filename: Name of the audio file (for API)
            
        Returns:
            Transcribed text
            
        Raises:
            OpenAIServiceError: If transcription fails after retries
            OpenAIRateLimitError: If rate limit is exceeded
        """
        start_time = time.time()
        logger.info(
            "audio_transcription_started",
            audio_size_bytes=len(audio_file),
            audio_size_mb=round(len(audio_file) / (1024 * 1024), 2),
            filename=filename
        )
        
        def _transcribe():
            # Create a file-like object from bytes
            from io import BytesIO
            audio_buffer = BytesIO(audio_file)
            audio_buffer.name = filename
            
            # Transcribe using Whisper
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_buffer
            )
            
            return transcript.text
        
        text = self._retry_with_backoff(_transcribe, "audio transcription")
        
        duration = time.time() - start_time
        logger.info(
            "audio_transcription_completed",
            transcribed_text_length=len(text),
            transcribed_words=len(text.split()),
            duration_seconds=round(duration, 2)
        )
        
        return text
    
    def generate_speech(
        self,
        text: str,
        voice: str = "alloy",
        model: str = "tts-1"
    ) -> bytes:
        """
        Generate speech audio from text using OpenAI TTS API.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            model: TTS model to use (tts-1 or tts-1-hd)
            
        Returns:
            Audio file content as bytes
            
        Raises:
            OpenAIServiceError: If speech generation fails after retries
            OpenAIRateLimitError: If rate limit is exceeded
        """
        start_time = time.time()
        logger.info(
            "speech_generation_started",
            text_length=len(text),
            text_words=len(text.split()),
            voice=voice,
            model=model
        )
        
        def _generate_speech():
            response = self.client.audio.speech.create(
                model=model,
                voice=voice,
                input=text
            )
            
            # Read the audio content
            return response.content
        
        audio_content = self._retry_with_backoff(_generate_speech, "speech generation")
        
        duration = time.time() - start_time
        logger.info(
            "speech_generation_completed",
            audio_size_bytes=len(audio_content),
            audio_size_mb=round(len(audio_content) / (1024 * 1024), 2),
            duration_seconds=round(duration, 2)
        )
        
        return audio_content
    
    def _retry_with_backoff(self, func, operation_name: str):
        """
        Execute function with exponential backoff retry logic.
        
        Args:
            func: Function to execute
            operation_name: Name of the operation (for logging)
            
        Returns:
            Result of the function
            
        Raises:
            OpenAIServiceError: If all retries fail
            OpenAIRateLimitError: If rate limit is exceeded
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func()
                
            except RateLimitError as e:
                logger.warning(
                    "openai_rate_limit_exceeded",
                    operation=operation_name,
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=str(e)
                )
                
                # Check if we have Retry-After header
                retry_after = getattr(e, 'retry_after', None)
                if retry_after:
                    wait_time = float(retry_after)
                else:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                
                if attempt < self.max_retries - 1:
                    logger.info(
                        "retry_scheduled",
                        operation=operation_name,
                        wait_seconds=wait_time,
                        attempt=attempt + 1
                    )
                    time.sleep(wait_time)
                    last_exception = e
                else:
                    raise OpenAIRateLimitError(
                        f"Rate limit exceeded after {self.max_retries} attempts"
                    ) from e
                    
            except (APIError, APITimeoutError) as e:
                logger.warning(
                    "openai_api_error",
                    operation=operation_name,
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=str(e),
                    error_type=type(e).__name__
                )
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    logger.info(
                        "retry_scheduled",
                        operation=operation_name,
                        wait_seconds=wait_time,
                        attempt=attempt + 1
                    )
                    time.sleep(wait_time)
                    last_exception = e
                else:
                    raise OpenAIServiceError(
                        f"{operation_name} failed after {self.max_retries} attempts: {str(e)}"
                    ) from e
                    
            except Exception as e:
                logger.error(
                    "openai_unexpected_error",
                    operation=operation_name,
                    attempt=attempt + 1,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True
                )
                raise OpenAIServiceError(
                    f"Unexpected error during {operation_name}: {str(e)}"
                ) from e
        
        # This should not be reached, but just in case
        if last_exception:
            raise OpenAIServiceError(
                f"{operation_name} failed after {self.max_retries} attempts"
            ) from last_exception
