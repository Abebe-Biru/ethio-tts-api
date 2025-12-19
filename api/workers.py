"""
Background Worker Module

This module handles background processing of async TTS jobs.
The worker runs as an asyncio task and processes jobs from the queue.
"""

import asyncio
import structlog
from datetime import datetime
from typing import Optional

from api.models import JobStatus
from api import jobs
from api.utils import sync_generate

log = structlog.get_logger()

# Worker state
_worker_task: Optional[asyncio.Task] = None
_worker_running = False

# ============================================================================
# BACKGROUND WORKER
# ============================================================================

async def process_job(job_id: str, model_manager, cache, storage, settings=None) -> bool:
    """
    Process a single TTS job.
    
    Args:
        job_id: Job identifier
        model_manager: Model manager instance
        cache: Cache instance
        storage: Storage instance for saving audio files
        
    Returns:
        True if successful, False otherwise
    """
    job = jobs.get_job(job_id)
    if not job:
        log.warning("job_not_found_for_processing", job_id=job_id)
        return False
    
    # Check if job was cancelled
    if job.status == JobStatus.CANCELLED:
        log.info("job_cancelled_skipping", job_id=job_id)
        return False
    
    # Update status to processing
    jobs.update_job_status(
        job_id,
        JobStatus.PROCESSING,
        started_at=datetime.utcnow()
    )
    log.info("job_processing_started", job_id=job_id, language=job.language, text_length=len(job.text))
    
    try:
        # Ensure model is loaded first
        from api.utils import get_model_for_language
        from api.config import get_settings
        if settings is None:
            settings = get_settings()
        await get_model_for_language(job.language, model_manager, settings)
        
        # Generate TTS audio (run in thread to avoid blocking)
        import anyio
        buffer = await anyio.to_thread.run_sync(
            sync_generate,
            job.text,
            job.language,
            model_manager
        )
        
        # Save audio file
        audio_path = await storage.save_audio(job_id, buffer)
        audio_url = f"/v1/download/{job_id}"
        
        # Update job status to completed
        jobs.update_job_status(
            job_id,
            JobStatus.COMPLETED,
            completed_at=datetime.utcnow(),
            audio_url=audio_url
        )
        
        duration = (datetime.utcnow() - job.started_at).total_seconds()
        
        log.info(
            "job_completed",
            job_id=job_id,
            language=job.language,
            audio_path=audio_path,
            duration=duration
        )
        
        # Track metrics
        from api.middleware.metrics import track_job_completed
        track_job_completed(job.language, "completed", duration)
        
        # Send webhook notification
        from api.webhooks import send_webhook
        await send_webhook(job_id)
        
        return True
        
    except Exception as e:
        # Update job status to failed
        error_message = str(e)
        jobs.update_job_status(
            job_id,
            JobStatus.FAILED,
            completed_at=datetime.utcnow(),
            error_message=error_message
        )
        
        duration = (datetime.utcnow() - job.started_at).total_seconds() if job.started_at else 0
        
        log.error(
            "job_failed",
            job_id=job_id,
            error=error_message,
            language=job.language,
            duration=duration
        )
        
        # Track metrics
        from api.middleware.metrics import track_job_completed
        track_job_completed(job.language, "failed", duration)
        
        # Send webhook notification for failure
        try:
            from api.webhooks import send_webhook
            await send_webhook(job_id)
        except Exception as webhook_error:
            log.error("webhook_failed_after_job_failure", job_id=job_id, error=str(webhook_error))
        
        return False


async def worker_loop(model_manager, cache, storage):
    """
    Main worker loop that processes jobs from the queue.
    
    Args:
        model_manager: Model manager instance
        cache: Cache instance
        storage: Storage instance
    """
    global _worker_running
    _worker_running = True
    
    log.info("background_worker_started")
    
    while _worker_running:
        try:
            # Get next job from queue
            job_id = jobs.get_next_job_id()
            
            if job_id:
                log.info("processing_job_from_queue", job_id=job_id, queue_length=jobs.get_queue_length())
                from api.config import get_settings
                settings = get_settings()
                await process_job(job_id, model_manager, cache, storage, settings)
            else:
                # No jobs in queue, wait a bit
                await asyncio.sleep(1)
            
            # Update queue metrics
            from api.middleware.metrics import update_queue_metrics
            update_queue_metrics(jobs.get_queue_length(), jobs.get_pending_jobs_count())
                
        except Exception as e:
            log.error("worker_loop_error", error=str(e))
            await asyncio.sleep(5)  # Wait before retrying
    
    log.info("background_worker_stopped")


# ============================================================================
# WORKER LIFECYCLE MANAGEMENT
# ============================================================================

def start_worker(model_manager, cache, storage):
    """
    Start the background worker.
    
    Args:
        model_manager: Model manager instance
        cache: Cache instance
        storage: Storage instance
        
    Returns:
        asyncio.Task: Worker task
    """
    global _worker_task, _worker_running
    
    if _worker_task and not _worker_task.done():
        log.warning("worker_already_running")
        return _worker_task
    
    _worker_running = True
    _worker_task = asyncio.create_task(worker_loop(model_manager, cache, storage))
    log.info("worker_task_created")
    
    return _worker_task


def stop_worker():
    """
    Stop the background worker gracefully.
    """
    global _worker_running, _worker_task
    
    _worker_running = False
    log.info("worker_stop_requested")
    
    if _worker_task:
        _worker_task.cancel()
        log.info("worker_task_cancelled")


def is_worker_running() -> bool:
    """
    Check if worker is running.
    
    Returns:
        True if worker is running, False otherwise
    """
    return _worker_running and _worker_task and not _worker_task.done()


def get_worker_status() -> dict:
    """
    Get worker status information.
    
    Returns:
        Dict with worker status
    """
    return {
        "running": is_worker_running(),
        "queue_length": jobs.get_queue_length(),
        "pending_jobs": jobs.get_pending_jobs_count(),
        "total_jobs": jobs.get_total_jobs()
    }


# ============================================================================
# JOB TIMEOUT HANDLER
# ============================================================================

async def check_stuck_jobs():
    """
    Check for jobs stuck in processing state and mark them as failed.
    This should be called periodically (e.g., every 5 minutes).
    """
    from datetime import timedelta
    
    timeout_minutes = 10
    now = datetime.utcnow()
    
    all_jobs = jobs.list_jobs(skip=0, limit=1000)
    stuck_count = 0
    
    for job in all_jobs:
        if job.status == JobStatus.PROCESSING and job.started_at:
            duration = now - job.started_at
            if duration > timedelta(minutes=timeout_minutes):
                jobs.update_job_status(
                    job.job_id,
                    JobStatus.FAILED,
                    completed_at=now,
                    error_message=f"Job timed out after {timeout_minutes} minutes"
                )
                stuck_count += 1
                log.warning("job_timeout", job_id=job.job_id, duration_minutes=duration.total_seconds() / 60)
    
    if stuck_count > 0:
        log.info("stuck_jobs_cleaned", count=stuck_count)
    
    return stuck_count
