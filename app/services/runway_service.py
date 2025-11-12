"""
Runway API Service for image generation and animation.
Handles integration with Runway API for creating images and animating them into videos.
"""

import time
import logging
import structlog
import requests
from typing import Optional, Dict, Any
from enum import Enum


logger = structlog.get_logger(__name__)


class TaskStatus(Enum):
    """Runway task status enumeration"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RunwayService:
    """Service for interacting with Runway API"""
    
    def __init__(self, api_key: str):
        """
        Initialize Runway service with API key.
        
        Args:
            api_key: Runway API key for authentication
        """
        self.api_key = api_key
        self.base_url = "https://api.runwayml.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.max_retries = 2
        self.timeout_seconds = 300  # 5 minutes
        self.polling_interval = 5  # 5 seconds
        
        logger.info(
            "runway_service_initialized",
            max_retries=self.max_retries,
            timeout_seconds=self.timeout_seconds,
            polling_interval=self.polling_interval
        )
    
    def generate_image(self, prompt: str) -> str:
        """
        Generate an image from a text prompt.
        
        Args:
            prompt: Text description for image generation
            
        Returns:
            task_id: Runway task ID for tracking generation progress
            
        Raises:
            Exception: If image generation request fails after retries
        """
        endpoint = f"{self.base_url}/images/generate"
        payload = {
            "prompt": prompt,
            "model": "gen3",
            "width": 1920,
            "height": 1080
        }
        
        start_time = time.time()
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(
                    "runway_image_generation_attempt",
                    attempt=attempt + 1,
                    max_attempts=self.max_retries + 1,
                    prompt_preview=prompt[:100]
                )
                
                response = requests.post(
                    endpoint,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    task_id = data.get("id")
                    duration = time.time() - start_time
                    logger.info(
                        "runway_image_task_created",
                        task_id=task_id,
                        duration_seconds=round(duration, 2)
                    )
                    return task_id
                elif response.status_code == 429:
                    # Rate limit - wait before retry
                    wait_time = 10 * (attempt + 1)
                    logger.warning(
                        "runway_rate_limited",
                        operation="image_generation",
                        wait_seconds=wait_time,
                        attempt=attempt + 1
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        "runway_image_generation_failed",
                        status_code=response.status_code,
                        response=response.text[:500],
                        attempt=attempt + 1
                    )
                    
                    if attempt == self.max_retries:
                        raise Exception(
                            f"Failed to generate image: {response.status_code} - {response.text}"
                        )
                    
                    time.sleep(5 * (attempt + 1))
                    
            except requests.exceptions.RequestException as e:
                logger.error(
                    "runway_request_error",
                    operation="image_generation",
                    error=str(e),
                    error_type=type(e).__name__,
                    attempt=attempt + 1,
                    exc_info=True
                )
                
                if attempt == self.max_retries:
                    raise Exception(f"Failed to generate image after {self.max_retries + 1} attempts: {str(e)}")
                
                time.sleep(5 * (attempt + 1))
        
        raise Exception("Failed to generate image: max retries exceeded")

    def animate_image(self, image_url: str, animation_prompt: str) -> str:
        """
        Animate an image into a 5-second video.
        
        Args:
            image_url: URL of the image to animate
            animation_prompt: Text description for animation style
            
        Returns:
            task_id: Runway task ID for tracking animation progress
            
        Raises:
            Exception: If animation request fails after retries
        """
        endpoint = f"{self.base_url}/images/animate"
        payload = {
            "image_url": image_url,
            "prompt": animation_prompt,
            "duration": 5,
            "model": "gen3"
        }
        
        start_time = time.time()
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(
                    "runway_animation_attempt",
                    attempt=attempt + 1,
                    max_attempts=self.max_retries + 1,
                    image_url=image_url,
                    prompt_preview=animation_prompt[:100]
                )
                
                response = requests.post(
                    endpoint,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    task_id = data.get("id")
                    duration = time.time() - start_time
                    logger.info(
                        "runway_animation_task_created",
                        task_id=task_id,
                        duration_seconds=round(duration, 2)
                    )
                    return task_id
                elif response.status_code == 429:
                    # Rate limit - wait before retry
                    wait_time = 10 * (attempt + 1)
                    logger.warning(
                        "runway_rate_limited",
                        operation="animation",
                        wait_seconds=wait_time,
                        attempt=attempt + 1
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        "runway_animation_failed",
                        status_code=response.status_code,
                        response=response.text[:500],
                        attempt=attempt + 1
                    )
                    
                    if attempt == self.max_retries:
                        raise Exception(
                            f"Failed to animate image: {response.status_code} - {response.text}"
                        )
                    
                    time.sleep(5 * (attempt + 1))
                    
            except requests.exceptions.RequestException as e:
                logger.error(
                    "runway_request_error",
                    operation="animation",
                    error=str(e),
                    error_type=type(e).__name__,
                    attempt=attempt + 1,
                    exc_info=True
                )
                
                if attempt == self.max_retries:
                    raise Exception(f"Failed to animate image after {self.max_retries + 1} attempts: {str(e)}")
                
                time.sleep(5 * (attempt + 1))
        
        raise Exception("Failed to animate image: max retries exceeded")
    
    def check_task_status(self, task_id: str) -> TaskStatus:
        """
        Check the status of a Runway task using polling.
        
        Args:
            task_id: Runway task ID to check
            
        Returns:
            TaskStatus: Current status of the task
            
        Raises:
            Exception: If status check fails
        """
        endpoint = f"{self.base_url}/tasks/{task_id}"
        
        try:
            response = requests.get(
                endpoint,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                status_str = data.get("status", "PENDING").upper()
                
                try:
                    status = TaskStatus[status_str]
                    logger.debug(
                        "runway_task_status_checked",
                        task_id=task_id,
                        status=status.value
                    )
                    return status
                except KeyError:
                    logger.warning(
                        "runway_unknown_status",
                        task_id=task_id,
                        status=status_str
                    )
                    return TaskStatus.PENDING
            else:
                logger.error(
                    "runway_status_check_failed",
                    task_id=task_id,
                    status_code=response.status_code,
                    response=response.text[:500]
                )
                raise Exception(f"Failed to check task status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(
                "runway_status_check_error",
                task_id=task_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise Exception(f"Failed to check task status: {str(e)}")

    def download_result(self, task_id: str, output_path: str) -> str:
        """
        Download the result of a completed Runway task.
        Waits for task completion with polling and timeout.
        
        Args:
            task_id: Runway task ID to download result from
            output_path: Local file path to save the result
            
        Returns:
            output_path: Path to the downloaded file
            
        Raises:
            Exception: If download fails or task times out
        """
        start_time = time.time()
        
        # Poll for task completion
        while True:
            elapsed_time = time.time() - start_time
            
            if elapsed_time > self.timeout_seconds:
                logger.error(
                    "runway_task_timeout",
                    task_id=task_id,
                    timeout_seconds=self.timeout_seconds,
                    elapsed_seconds=round(elapsed_time, 2)
                )
                raise Exception(f"Task timeout: exceeded {self.timeout_seconds} seconds")
            
            status = self.check_task_status(task_id)
            
            if status == TaskStatus.SUCCEEDED:
                logger.info(
                    "runway_task_completed",
                    task_id=task_id,
                    duration_seconds=round(elapsed_time, 2)
                )
                break
            elif status == TaskStatus.FAILED:
                logger.error(
                    "runway_task_failed",
                    task_id=task_id,
                    duration_seconds=round(elapsed_time, 2)
                )
                raise Exception(f"Task failed: {task_id}")
            elif status == TaskStatus.CANCELLED:
                logger.error(
                    "runway_task_cancelled",
                    task_id=task_id,
                    duration_seconds=round(elapsed_time, 2)
                )
                raise Exception(f"Task cancelled: {task_id}")
            else:
                # Task still running or pending
                logger.debug(
                    "runway_task_polling",
                    task_id=task_id,
                    status=status.value,
                    elapsed_seconds=round(elapsed_time, 2)
                )
                time.sleep(self.polling_interval)
        
        # Get result URL
        endpoint = f"{self.base_url}/tasks/{task_id}"
        
        try:
            response = requests.get(
                endpoint,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get task result: {response.status_code}")
            
            data = response.json()
            result_url = data.get("output", {}).get("url")
            
            if not result_url:
                raise Exception("No result URL in task response")
            
            download_start = time.time()
            logger.info(
                "runway_download_started",
                task_id=task_id,
                result_url=result_url,
                output_path=output_path
            )
            
            # Download the file
            download_response = requests.get(result_url, timeout=60, stream=True)
            
            if download_response.status_code != 200:
                raise Exception(f"Failed to download result: {download_response.status_code}")
            
            # Save to file
            bytes_downloaded = 0
            with open(output_path, 'wb') as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
            
            download_duration = time.time() - download_start
            file_size_mb = bytes_downloaded / (1024 * 1024)
            
            logger.info(
                "runway_download_completed",
                task_id=task_id,
                output_path=output_path,
                file_size_mb=round(file_size_mb, 2),
                duration_seconds=round(download_duration, 2)
            )
            return output_path
            
        except requests.exceptions.RequestException as e:
            logger.error(
                "runway_download_error",
                task_id=task_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise Exception(f"Failed to download result: {str(e)}")
