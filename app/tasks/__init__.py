"""
Celery tasks module for asynchronous video generation.
Configures Celery app with Redis broker and scheduled tasks.
"""
import logging
from celery import Celery
from celery.schedules import crontab

from app.config import Config


logger = logging.getLogger(__name__)


# Initialize Celery app
celery_app = Celery(
    'ai_video_generator',
    broker=Config.REDIS_URL,
    backend=Config.REDIS_URL,
    include=['app.tasks.video_generation']
)

# Configure Celery
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minutes soft limit
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
    },
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    
    # Worker settings
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    worker_disable_rate_limits=False,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'cleanup-old-files-hourly': {
            'task': 'app.tasks.cleanup_old_files',
            'schedule': crontab(minute=0),  # Run every hour at minute 0
            'options': {
                'expires': 3600,  # Task expires after 1 hour if not executed
            }
        },
    },
)

logger.info(
    f"Celery app initialized with broker: {Config.REDIS_URL[:20]}... "
    f"(scheduled tasks: cleanup_old_files)"
)


@celery_app.task(name='app.tasks.cleanup_old_files', bind=True)
def cleanup_old_files(self):
    """
    Scheduled task to cleanup old temporary files.
    
    Runs every hour to remove job directories older than FILE_CLEANUP_HOURS.
    This prevents disk space from filling up with abandoned or completed jobs.
    
    Returns:
        dict: Cleanup statistics with count of removed directories
    """
    from app.utils.file_manager import FileManager
    
    try:
        logger.info("Starting scheduled cleanup of old files")
        
        file_manager = FileManager()
        cleaned_count = file_manager.cleanup_old_files(
            max_age_hours=Config.FILE_CLEANUP_HOURS
        )
        
        # Get disk usage after cleanup
        disk_usage = file_manager.get_disk_usage()
        
        result = {
            'cleaned_count': cleaned_count,
            'disk_usage_mb': disk_usage['total_size_mb'],
            'remaining_jobs': disk_usage['job_count']
        }
        
        logger.info(
            f"Cleanup completed: removed {cleaned_count} directories, "
            f"disk usage: {disk_usage['total_size_mb']} MB, "
            f"remaining jobs: {disk_usage['job_count']}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error during scheduled cleanup: {e}", exc_info=True)
        # Don't raise - cleanup failures shouldn't crash the worker
        return {
            'error': str(e),
            'cleaned_count': 0
        }


# Export celery app for worker
__all__ = ['celery_app', 'cleanup_old_files']
