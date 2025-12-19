"""
API v1 Routes - Versioned endpoints for TTS API
"""
from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional
import structlog
import io
import hashlib
import base64
import anyio
from tqdm.contrib.concurrent import thread_map

from ..models import TTSRequest, BatchTTSRequest, AsyncTTSRequest, JobCreateResponse, JobResponse, JobListResponse
from ..config import get_settings
from ..utils import get_model_for_language, sync_generate, process_single_text
from .. import jobs

log = structlog.get_logger()
settings = get_settings()

# Create v1 router
router = APIRouter(prefix="/v1", tags=["v1"])

@router.get("/health")
async def health_check_v1():
    """
    V1 Health Check - Enhanced with version info
    """
    from ..main import model_manager, cache
    
    loaded_languages = model_manager.get_loaded_languages() if model_manager else []
    supported_languages = list(settings.supported_languages.keys())
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "api_version": "v1",
        "model_loaded": len(loaded_languages) > 0,
        "cache_size": len(cache) if cache else 0,
        "supported_languages": supported_languages,
        "loaded_languages": loaded_languages,
        "default_language": settings.default_language
    }


@router.get("/languages")
async def get_languages_v1():
    """
    V1 Get Languages - List all supported languages
    """
    from ..main import model_manager
    
    if not model_manager:
        return {"error": "Model manager not initialized"}
    
    supported = model_manager.get_supported_languages()
    loaded = model_manager.get_loaded_languages()
    
    languages_info = {}
    for lang_code, model_name in supported.items():
        languages_info[lang_code] = {
            "model_name": model_name,
            "loaded": lang_code in loaded,
            "is_default": lang_code == settings.default_language
        }
    
    return {
        "supported_languages": languages_info,
        "default_language": settings.default_language,
        "loaded_count": len(loaded),
        "total_count": len(supported)
    }


@router.post("/languages/{language}/load")
async def load_language_model_v1(language: str):
    """
    V1 Load Language Model - Preload a language model
    """
    from ..main import model_manager
    
    if not model_manager:
        raise HTTPException(status_code=500, detail="Model manager not initialized")
    
    try:
        if language not in settings.supported_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language '{language}'. Supported: {list(settings.supported_languages.keys())}"
            )
        
        if model_manager.is_model_loaded(language):
            return {
                "message": f"Model for '{language}' is already loaded",
                "language": language,
                "status": "already_loaded"
            }
        
        await model_manager.load_model(language)
        return {
            "message": f"Model for '{language}' loaded successfully",
            "language": language,
            "status": "loaded"
        }
        
    except Exception as e:
        log.error("manual_model_load_failed", language=language, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")


@router.post("/tts")
async def generate_speech_v1(
    request: TTSRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    V1 Generate Speech - Convert text to speech
    
    Enhanced with:
    - API key support (optional for now)
    - Better error messages
    - Structured responses
    """
    from ..main import model_manager, cache
    
    if not request.text.strip():
        log.warning("empty_text_request", api_version="v1")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "empty_text",
                "message": "Text input cannot be empty",
                "field": "text"
            }
        )
    
    language = request.language or settings.default_language
    log.info("tts_request_received", text_length=len(request.text), language=language, api_version="v1")
    
    try:
        # Ensure model is loaded
        await get_model_for_language(language, model_manager, settings)
        
        # Generate cache key
        text_hash = hashlib.md5(f"{language}:{request.text}".encode()).hexdigest()
        cache_key = f"waveform_{language}_{text_hash}"
        
        # Check cache
        if cache_key in cache:
            waveform_bytes = cache[cache_key]
            log.info("cache_hit", cache_key=cache_key, language=language, api_version="v1")
            
            filename = f"{language}_speech.wav"
            return StreamingResponse(
                io.BytesIO(waveform_bytes),
                media_type="audio/wav",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "X-Cache": "HIT",
                    "X-Language": language,
                    "X-API-Version": "v1"
                }
            )
        
        # Generate new audio
        buffer = await anyio.to_thread.run_sync(sync_generate, request.text, language, model_manager)
        
        # Cache the result
        waveform_bytes = buffer.getvalue()
        cache[cache_key] = waveform_bytes
        
        log.info("tts_generated", text_length=len(request.text), language=language, api_version="v1")
        
        filename = f"{language}_speech.wav"
        return StreamingResponse(
            buffer,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Cache": "MISS",
                "X-Language": language,
                "X-API-Version": "v1"
            }
        )
        
    except Exception as e:
        log.error("tts_generation_failed", error=str(e), text_length=len(request.text), language=language, api_version="v1")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "generation_failed",
                "message": f"Error generating speech: {str(e)}",
                "language": language
            }
        )


@router.post("/batch_tts")
async def generate_batch_speech_v1(request: BatchTTSRequest):
    """
    V1 Batch Generate Speech - Convert multiple texts to speech
    """
    from ..main import model_manager, cache
    
    if not request.texts:
        log.warning("empty_batch_request", api_version="v1")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "empty_batch",
                "message": "Texts list cannot be empty",
                "field": "texts"
            }
        )
    
    language = request.language or settings.default_language
    log.info("batch_tts_request_received", num_texts=len(request.texts), language=language, api_version="v1")
    
    try:
        # Ensure model is loaded
        await get_model_for_language(language, model_manager, settings)
        
        # Check cache for each text
        cached_results = []
        to_process = []
        
        for text in request.texts:
            text_hash = hashlib.md5(f"{language}:{text}".encode()).hexdigest()
            cache_key = f"waveform_{language}_{text_hash}"
            if cache_key in cache:
                waveform_bytes = cache[cache_key]
                cached_results.append({
                    "hash": text_hash,
                    "audio_b64": base64.b64encode(waveform_bytes).decode('utf-8'),
                    "cached": True
                })
                log.debug("batch_cache_hit", cache_key=cache_key, language=language, api_version="v1")
            else:
                to_process.append(text)
        
        # Process uncached texts
        if to_process:
            def run_batch():
                return thread_map(
                    lambda text: {**process_single_text(text, language, model_manager, cache), "cached": False},
                    to_process,
                    max_workers=4,
                    disable=(not settings.debug)
                )
            
            new_results = await anyio.to_thread.run_sync(run_batch)
            cached_results.extend(new_results)
            log.info("batch_generated", num_new=len(to_process), language=language, api_version="v1")
        
        return JSONResponse(content={
            "results": cached_results,
            "total": len(request.texts),
            "cached": len(request.texts) - len(to_process),
            "generated": len(to_process),
            "language": language
        })
        
    except Exception as e:
        log.error("batch_tts_failed", error=str(e), num_texts=len(request.texts), language=language, api_version="v1")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "batch_generation_failed",
                "message": f"Error generating batch speech: {str(e)}",
                "language": language
            }
        )


# ============================================================================
# ASYNC JOB ENDPOINTS (Webhooks Feature)
# ============================================================================

@router.post("/tts/async", response_model=JobCreateResponse, status_code=202)
async def create_async_tts_job(
    request: AsyncTTSRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    Create Async TTS Job - Submit a long-running TTS job
    
    This endpoint creates an async job and returns immediately with a job_id.
    The job will be processed in the background, and a webhook notification
    will be sent to the provided webhook_url when complete.
    
    Args:
        request: AsyncTTSRequest with text, language, and webhook_url
        x_api_key: Optional API key for authentication
        
    Returns:
        JobCreateResponse with job_id, status, and created_at
        
    Status Codes:
        202: Job created and queued successfully
        400: Invalid request (bad webhook_url, empty text, etc.)
        429: Rate limit exceeded
    """
    # Validate text
    if not request.text.strip():
        log.warning("async_empty_text", api_version="v1")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "empty_text",
                "message": "Text input cannot be empty",
                "field": "text"
            }
        )
    
    # Validate language
    language = request.language or settings.default_language
    if language not in settings.supported_languages:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "unsupported_language",
                "message": f"Language '{language}' is not supported",
                "supported": list(settings.supported_languages.keys())
            }
        )
    
    # Check pending jobs limit (prevent queue overflow)
    pending_count = jobs.get_pending_jobs_count()
    if pending_count >= 100:
        log.warning("job_queue_full", pending_count=pending_count)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "queue_full",
                "message": "Too many pending jobs. Please try again later.",
                "pending_jobs": pending_count,
                "max_pending": 100
            }
        )
    
    try:
        # Create job
        job = jobs.create_job(
            text=request.text,
            language=language,
            webhook_url=str(request.webhook_url)
        )
        
        # Track metrics
        from ..middleware.metrics import track_job_created, update_queue_metrics
        track_job_created(language)
        update_queue_metrics(jobs.get_queue_length(), jobs.get_pending_jobs_count())
        
        log.info(
            "async_job_created",
            job_id=job.job_id,
            text_length=len(request.text),
            language=language,
            queue_length=jobs.get_queue_length(),
            api_version="v1"
        )
        
        return JobCreateResponse(
            job_id=job.job_id,
            status=job.status,
            message="Job created and queued for processing",
            created_at=job.created_at
        )
        
    except Exception as e:
        log.error("async_job_creation_failed", error=str(e), api_version="v1")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "job_creation_failed",
                "message": f"Failed to create job: {str(e)}"
            }
        )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """
    Get Job Status - Check the status of an async TTS job
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        JobResponse with job details and current status
        
    Status Codes:
        200: Job found
        404: Job not found
    """
    job = jobs.get_job(job_id)
    
    if not job:
        log.warning("job_not_found", job_id=job_id, api_version="v1")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "job_not_found",
                "message": f"Job '{job_id}' not found",
                "job_id": job_id
            }
        )
    
    log.info("job_status_retrieved", job_id=job_id, status=job.status, api_version="v1")
    
    return JobResponse(
        job_id=job.job_id,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        audio_url=job.audio_url,
        error_message=job.error_message
    )


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(page: int = 1, page_size: int = 20):
    """
    List Jobs - Get all async TTS jobs with pagination
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of jobs per page (max 100)
        
    Returns:
        JobListResponse with list of jobs and pagination info
        
    Status Codes:
        200: Jobs retrieved successfully
        400: Invalid pagination parameters
    """
    # Validate pagination
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_page",
                "message": "Page number must be >= 1",
                "field": "page"
            }
        )
    
    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_page_size",
                "message": "Page size must be between 1 and 100",
                "field": "page_size"
            }
        )
    
    # Calculate skip
    skip = (page - 1) * page_size
    
    # Get jobs
    job_list = jobs.list_jobs(skip=skip, limit=page_size)
    total = jobs.get_total_jobs()
    
    # Convert to response models
    job_responses = [
        JobResponse(
            job_id=job.job_id,
            status=job.status,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            audio_url=job.audio_url,
            error_message=job.error_message
        )
        for job in job_list
    ]
    
    log.info("jobs_listed", page=page, page_size=page_size, total=total, api_version="v1")
    
    return JobListResponse(
        jobs=job_responses,
        total=total,
        page=page,
        page_size=page_size
    )



@router.get("/download/{job_id}")
async def download_audio(job_id: str):
    """
    Download Audio - Get the generated audio file for a completed job
    
    Args:
        job_id: Job identifier
        
    Returns:
        Audio file (WAV format)
        
    Status Codes:
        200: Audio file found and returned
        404: Job not found or audio not available
        410: Audio file expired (deleted after 24 hours)
    """
    from ..storage import get_storage
    
    # Check if job exists
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "job_not_found",
                "message": f"Job '{job_id}' not found",
                "job_id": job_id
            }
        )
    
    # Check if job is completed
    if job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "job_not_completed",
                "message": f"Job is in '{job.status}' state. Audio only available for completed jobs.",
                "job_id": job_id,
                "status": job.status
            }
        )
    
    # Get audio file
    storage = get_storage()
    audio_path = storage.get_audio_path(job_id)
    
    if not audio_path or not audio_path.exists():
        raise HTTPException(
            status_code=410,
            detail={
                "error": "audio_expired",
                "message": "Audio file has expired or been deleted",
                "job_id": job_id,
                "note": "Audio files are automatically deleted after 24 hours"
            }
        )
    
    # Read and return audio file
    try:
        with open(audio_path, 'rb') as f:
            audio_data = f.read()
        
        log.info("audio_downloaded", job_id=job_id, size_bytes=len(audio_data))
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename={job_id}.wav",
                "X-Job-ID": job_id,
                "X-Language": job.language,
                "X-API-Version": "v1"
            }
        )
        
    except Exception as e:
        log.error("audio_download_failed", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "error": "download_failed",
                "message": f"Failed to download audio: {str(e)}",
                "job_id": job_id
            }
        )



@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel Job - Cancel a pending async TTS job
    
    Only jobs with status "pending" can be cancelled.
    Jobs that are already processing, completed, or failed cannot be cancelled.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Success message with updated job status
        
    Status Codes:
        200: Job cancelled successfully
        404: Job not found
        409: Job cannot be cancelled (already processing/completed/failed)
    """
    from ..models import JobStatus
    
    # Get job
    job = jobs.get_job(job_id)
    
    if not job:
        log.warning("cancel_job_not_found", job_id=job_id, api_version="v1")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "job_not_found",
                "message": f"Job '{job_id}' not found",
                "job_id": job_id
            }
        )
    
    # Check if job can be cancelled
    # Note: job.status is a string because of use_enum_values=True in Job model
    if job.status != "pending":
        log.warning(
            "cancel_job_invalid_status",
            job_id=job_id,
            current_status=job.status,
            api_version="v1"
        )
        raise HTTPException(
            status_code=409,
            detail={
                "error": "cannot_cancel",
                "message": f"Job cannot be cancelled. Current status: {job.status}",
                "job_id": job_id,
                "status": job.status,
                "reason": "Only pending jobs can be cancelled"
            }
        )
    
    # Cancel the job
    from datetime import datetime
    jobs.update_job_status(
        job_id,
        JobStatus.CANCELLED,
        completed_at=datetime.utcnow()
    )
    
    # Remove from queue (but keep job record)
    jobs.remove_from_queue(job_id)
    
    log.info("job_cancelled", job_id=job_id, api_version="v1")
    
    # Send webhook notification for cancellation
    try:
        from ..webhooks import send_webhook
        await send_webhook(job_id)
    except Exception as e:
        log.error("webhook_failed_after_cancellation", job_id=job_id, error=str(e))
    
    return {
        "message": "Job cancelled successfully",
        "job_id": job_id,
        "status": "cancelled",
        "cancelled_at": datetime.utcnow().isoformat()
    }
