"""
Video Service for generating video segments.

This service coordinates the generation of all video segments by managing
the parallel creation of images and their animation through the Runway API.
"""

import logging
import structlog
import time
from typing import List, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.models.video_job import ScriptSegment, VideoSegment, SegmentStatus
from app.services.runway_service import RunwayService
from app.services.script_service import ScriptService
from app.utils.file_manager import FileManager


logger = structlog.get_logger(__name__)


class VideoService:
    """
    Service for generating video segments from script segments.
    
    Manages parallel generation of images and animations using Runway API,
    with progress tracking and error handling.
    """
    
    def __init__(
        self,
        runway_service: RunwayService,
        script_service: ScriptService,
        file_manager: FileManager,
        max_workers: int = 3
    ):
        """
        Initialize Video Service with dependencies.
        
        Args:
            runway_service: Service for Runway API interactions
            script_service: Service for script processing
            file_manager: Service for file management
            max_workers: Maximum number of parallel workers (default: 3)
        """
        self.runway_service = runway_service
        self.script_service = script_service
        self.file_manager = file_manager
        self.max_workers = max_workers
        
        logger.info(f"VideoService initialized with max_workers={max_workers}")
    
    def generate_all_segments(
        self,
        job_id: str,
        segments: List[ScriptSegment],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[VideoSegment]:
        """
        Generate all video segments with parallel processing.
        
        Creates images and animates them for all script segments using
        ThreadPoolExecutor for parallel processing. Sends progress updates
        every 10 segments.
        
        Args:
            job_id: Unique identifier for the job
            segments: List of script segments to process
            progress_callback: Optional callback function(current, total) for progress updates
            
        Returns:
            List of VideoSegment objects with generated content
            
        Raises:
            Exception: If generation fails for critical segments
            
        Requirements: 4.4, 4.5, 4.6, 5.4, 5.5, 5.6
        """
        start_time = time.time()
        
        logger.info(
            "segment_generation_started",
            job_id=job_id,
            segment_count=len(segments),
            max_workers=self.max_workers
        )
        
        video_segments = []
        failed_segments = []
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all segment generation tasks
            future_to_segment = {
                executor.submit(self.generate_segment, job_id, segment): segment
                for segment in segments
            }
            
            # Process completed tasks as they finish
            for future in as_completed(future_to_segment):
                segment = future_to_segment[future]
                
                try:
                    video_segment = future.result()
                    video_segments.append(video_segment)
                    
                    # Send progress update every 10 segments
                    if len(video_segments) % 10 == 0 and progress_callback:
                        progress_callback(len(video_segments), len(segments))
                        elapsed = time.time() - start_time
                        logger.info(
                            "segment_generation_progress",
                            job_id=job_id,
                            completed=len(video_segments),
                            total=len(segments),
                            percent=round((len(video_segments) / len(segments)) * 100, 1),
                            elapsed_seconds=round(elapsed, 2)
                        )
                    
                except Exception as e:
                    logger.error(
                        "segment_generation_failed",
                        job_id=job_id,
                        segment_index=segment.index,
                        error=str(e),
                        error_type=type(e).__name__,
                        exc_info=True
                    )
                    
                    # Create a failed segment entry
                    failed_segment = VideoSegment(
                        index=segment.index,
                        script_segment=segment,
                        status=SegmentStatus.FAILED
                    )
                    failed_segments.append(failed_segment)
                    video_segments.append(failed_segment)
        
        # Sort segments by index to maintain order
        video_segments.sort(key=lambda x: x.index)
        
        # Send final progress update
        if progress_callback:
            progress_callback(len(video_segments), len(segments))
        
        # Log summary
        total_duration = time.time() - start_time
        success_count = len([s for s in video_segments if s.status == SegmentStatus.VIDEO_READY])
        
        logger.info(
            "segment_generation_completed",
            job_id=job_id,
            success_count=success_count,
            failed_count=len(failed_segments),
            total_count=len(segments),
            duration_seconds=round(total_duration, 2),
            avg_time_per_segment=round(total_duration / len(segments), 2) if segments else 0
        )
        
        # If too many segments failed, raise an exception
        if len(failed_segments) > len(segments) * 0.2:  # More than 20% failed
            raise Exception(
                f"Too many segments failed: {len(failed_segments)}/{len(segments)}"
            )
        
        return video_segments
    
    def generate_segment(
        self,
        job_id: str,
        segment: ScriptSegment
    ) -> VideoSegment:
        """
        Generate a single video segment (image + animation).
        
        Process:
        1. Generate image from segment's image_prompt
        2. Wait for image generation to complete
        3. Animate the generated image
        4. Wait for animation to complete
        5. Download and save both image and video
        
        Args:
            job_id: Unique identifier for the job
            segment: Script segment to process
            
        Returns:
            VideoSegment with generated image and video paths
            
        Raises:
            Exception: If generation fails
            
        Requirements: 4.4, 4.5, 4.6, 5.4, 5.5, 5.6
        """
        segment_start_time = time.time()
        
        logger.info(
            "segment_generation_started",
            job_id=job_id,
            segment_index=segment.index,
            segment_text_preview=segment.text[:100]
        )
        
        video_segment = VideoSegment(
            index=segment.index,
            script_segment=segment,
            status=SegmentStatus.PENDING
        )
        
        try:
            # Step 1: Generate image
            image_start = time.time()
            video_segment.status = SegmentStatus.GENERATING_IMAGE
            logger.debug(
                "generating_image",
                job_id=job_id,
                segment_index=segment.index,
                prompt_preview=segment.image_prompt[:100]
            )
            
            image_task_id = self.runway_service.generate_image(segment.image_prompt)
            video_segment.runway_image_task_id = image_task_id
            
            # Step 2: Download generated image
            image_filename = f"segment_{segment.index:03d}_image.png"
            image_path = f"{self.file_manager.temp_dir}/{job_id}/images/{image_filename}"
            
            self.runway_service.download_result(image_task_id, image_path)
            video_segment.image_path = image_path
            video_segment.status = SegmentStatus.IMAGE_READY
            
            image_duration = time.time() - image_start
            logger.info(
                "image_generated",
                job_id=job_id,
                segment_index=segment.index,
                image_path=image_path,
                duration_seconds=round(image_duration, 2)
            )
            
            # Step 3: Animate image
            animation_start = time.time()
            video_segment.status = SegmentStatus.ANIMATING
            logger.debug(
                "animating_image",
                job_id=job_id,
                segment_index=segment.index,
                prompt_preview=segment.animation_prompt[:100]
            )
            
            # For animation, we need the image URL or path
            # In a real implementation, this would be uploaded to a CDN
            # For now, we'll use the local path (Runway API would need URL)
            video_task_id = self.runway_service.animate_image(
                image_path,
                segment.animation_prompt
            )
            video_segment.runway_video_task_id = video_task_id
            
            # Step 4: Download animated video
            video_filename = f"segment_{segment.index:03d}_video.mp4"
            video_path = f"{self.file_manager.temp_dir}/{job_id}/videos/{video_filename}"
            
            self.runway_service.download_result(video_task_id, video_path)
            video_segment.video_path = video_path
            video_segment.status = SegmentStatus.VIDEO_READY
            
            animation_duration = time.time() - animation_start
            total_segment_duration = time.time() - segment_start_time
            
            logger.info(
                "segment_completed",
                job_id=job_id,
                segment_index=segment.index,
                image_path=image_path,
                video_path=video_path,
                image_duration_seconds=round(image_duration, 2),
                animation_duration_seconds=round(animation_duration, 2),
                total_duration_seconds=round(total_segment_duration, 2)
            )
            
            return video_segment
            
        except Exception as e:
            segment_duration = time.time() - segment_start_time
            logger.error(
                "segment_generation_error",
                job_id=job_id,
                segment_index=segment.index,
                error=str(e),
                error_type=type(e).__name__,
                status=video_segment.status.value,
                duration_seconds=round(segment_duration, 2),
                exc_info=True
            )
            
            video_segment.status = SegmentStatus.FAILED
            raise Exception(
                f"Segment {segment.index} generation failed: {str(e)}"
            )
