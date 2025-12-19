"""
Job Management Module

This module handles CRUD operations for async TTS jobs.
For MVP, we use in-memory storage (dict). This can be easily migrated
to Redis or PostgreSQL later without changing the interface.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
from api.models import Job, JobStatus

# ============================================================================
# IN-MEMORY STORAGE (MVP)
# ============================================================================

# Job storage: {job_id: Job}
_jobs: Dict[str, Job] = {}

# Job queue for background processing
_job_queue: List[str] = []

# ============================================================================
# JOB CRUD OPERATIONS
# ============================================================================

def create_job(text: str, language: str, webhook_url: str) -> Job:
    """
    Create a new async TTS job.
    
    Args:
        text: Text to convert to speech
        language: Language for TTS generation
        webhook_url: URL to receive webhook notification
        
    Returns:
        Job: Created job object
    """
    job_id = f"job_{uuid.uuid4().hex[:16]}"
    
    job = Job(
        job_id=job_id,
        text=text,
        language=language,
        webhook_url=webhook_url,
        status=JobStatus.PENDING,
        created_at=datetime.utcnow()
    )
    
    _jobs[job_id] = job
    _job_queue.append(job_id)
    
    return job

def get_job(job_id: str) -> Optional[Job]:
    """
    Get a job by ID.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Job if found, None otherwise
    """
    return _jobs.get(job_id)

def update_job_status(
    job_id: str,
    status: JobStatus,
    started_at: Optional[datetime] = None,
    completed_at: Optional[datetime] = None,
    audio_url: Optional[str] = None,
    error_message: Optional[str] = None
) -> Optional[Job]:
    """
    Update job status and related fields.
    
    Args:
        job_id: Job identifier
        status: New job status
        started_at: Processing start timestamp (optional)
        completed_at: Completion timestamp (optional)
        audio_url: URL to download audio (optional)
        error_message: Error message if failed (optional)
        
    Returns:
        Updated Job if found, None otherwise
    """
    job = _jobs.get(job_id)
    if not job:
        return None
    
    job.status = status
    if started_at:
        job.started_at = started_at
    if completed_at:
        job.completed_at = completed_at
    if audio_url:
        job.audio_url = audio_url
    if error_message:
        job.error_message = error_message
    
    return job

def update_webhook_status(job_id: str, delivered: bool, attempts: int) -> Optional[Job]:
    """
    Update webhook delivery status.
    
    Args:
        job_id: Job identifier
        delivered: Whether webhook was successfully delivered
        attempts: Number of delivery attempts
        
    Returns:
        Updated Job if found, None otherwise
    """
    job = _jobs.get(job_id)
    if not job:
        return None
    
    job.webhook_delivered = delivered
    job.webhook_attempts = attempts
    
    return job

def list_jobs(skip: int = 0, limit: int = 100) -> List[Job]:
    """
    List all jobs with pagination.
    
    Args:
        skip: Number of jobs to skip
        limit: Maximum number of jobs to return
        
    Returns:
        List of jobs
    """
    all_jobs = list(_jobs.values())
    # Sort by created_at descending (newest first)
    all_jobs.sort(key=lambda j: j.created_at, reverse=True)
    return all_jobs[skip:skip + limit]

def get_total_jobs() -> int:
    """
    Get total number of jobs.
    
    Returns:
        Total job count
    """
    return len(_jobs)

def remove_from_queue(job_id: str) -> bool:
    """
    Remove a job from the processing queue (for cancellation).
    The job record is kept, but it won't be processed.
    
    Args:
        job_id: Job identifier
        
    Returns:
        True if removed from queue, False if not in queue
    """
    if job_id in _job_queue:
        _job_queue.remove(job_id)
        return True
    return False

def delete_job(job_id: str) -> bool:
    """
    Delete a job completely (removes from storage and queue).
    
    Args:
        job_id: Job identifier
        
    Returns:
        True if deleted, False if not found
    """
    if job_id in _jobs:
        del _jobs[job_id]
        # Remove from queue if present
        if job_id in _job_queue:
            _job_queue.remove(job_id)
        return True
    return False

# ============================================================================
# QUEUE OPERATIONS
# ============================================================================

def get_next_job_id() -> Optional[str]:
    """
    Get the next job ID from the queue (FIFO).
    
    Returns:
        Job ID if queue not empty, None otherwise
    """
    if _job_queue:
        return _job_queue.pop(0)
    return None

def get_queue_length() -> int:
    """
    Get current queue length.
    
    Returns:
        Number of jobs in queue
    """
    return len(_job_queue)

def get_pending_jobs_count() -> int:
    """
    Get count of jobs with pending status.
    
    Returns:
        Number of pending jobs
    """
    return sum(1 for job in _jobs.values() if job.status == JobStatus.PENDING)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def clear_all_jobs():
    """
    Clear all jobs and queue (for testing).
    WARNING: This deletes all data!
    """
    _jobs.clear()
    _job_queue.clear()
