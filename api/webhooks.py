"""
Webhook Delivery Module

This module handles sending webhook notifications to user-provided URLs.
Includes retry logic and HMAC-SHA256 signature generation for security.
"""

import hmac
import hashlib
import json
import httpx
import structlog
from typing import Optional
from datetime import datetime

from api import jobs

log = structlog.get_logger()

# ============================================================================
# WEBHOOK CONFIGURATION
# ============================================================================

def get_webhook_secret() -> str:
    """Get webhook secret from config"""
    from api.config import get_settings
    return get_settings().webhook_secret

# ============================================================================
# SIGNATURE GENERATION
# ============================================================================

def generate_webhook_signature(payload: dict, timestamp: int, secret: str = None) -> str:
    """
    Generate HMAC-SHA256 signature for webhook payload.
    
    The signature is computed as:
    HMAC-SHA256(secret, timestamp + "." + json_payload)
    
    Args:
        payload: Webhook payload dictionary
        timestamp: Unix timestamp
        secret: Secret key for HMAC
        
    Returns:
        Signature in format "sha256=<hex_digest>"
    """
    # Get secret from config if not provided
    if secret is None:
        secret = get_webhook_secret()
    
    # Create the message to sign: timestamp.payload
    payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    message = f"{timestamp}.{payload_json}"
    
    # Generate HMAC-SHA256 signature
    signature = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"sha256={signature}"


def verify_webhook_signature(payload: dict, timestamp: int, signature: str, secret: str = None) -> bool:
    """
    Verify webhook signature.
    
    Args:
        payload: Webhook payload dictionary
        timestamp: Unix timestamp from X-Webhook-Timestamp header
        signature: Signature from X-Webhook-Signature header
        secret: Secret key for HMAC
        
    Returns:
        True if signature is valid, False otherwise
    """
    # Get secret from config if not provided
    if secret is None:
        secret = get_webhook_secret()
    
    expected_signature = generate_webhook_signature(payload, timestamp, secret)
    return hmac.compare_digest(signature, expected_signature)


# ============================================================================
# WEBHOOK DELIVERY
# ============================================================================

async def send_webhook(job_id: str, max_retries: int = 3) -> bool:
    """
    Send webhook notification for a job.
    
    Args:
        job_id: Job identifier
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if webhook delivered successfully, False otherwise
    """
    job = jobs.get_job(job_id)
    if not job:
        log.warning("webhook_job_not_found", job_id=job_id)
        return False
    
    # Prepare webhook payload
    payload = {
        "job_id": job.job_id,
        "status": job.status,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "audio_url": job.audio_url,
        "error_message": job.error_message,
        "language": job.language,
        "text_length": len(job.text)
    }
    
    # Generate timestamp and signature
    timestamp = int(datetime.utcnow().timestamp())
    signature = generate_webhook_signature(payload, timestamp)
    
    # Track webhook delivery start time
    import time
    start_time = time.time()
    
    # Try sending webhook with retries
    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    job.webhook_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "TTS-API-Webhook/1.0",
                        "X-Webhook-Signature": signature,
                        "X-Webhook-Timestamp": str(timestamp),
                        "X-Webhook-ID": job.job_id,
                        "X-Webhook-Attempt": str(attempt)
                    }
                )
                
                if response.status_code in [200, 201, 202, 204]:
                    # Success
                    duration = time.time() - start_time
                    jobs.update_webhook_status(job_id, delivered=True, attempts=attempt)
                    
                    # Track metrics
                    from api.middleware.metrics import track_webhook_delivery
                    track_webhook_delivery(success=True, duration_seconds=duration, retry_count=attempt - 1)
                    
                    log.info(
                        "webhook_delivered",
                        job_id=job_id,
                        status_code=response.status_code,
                        attempt=attempt,
                        duration=duration
                    )
                    return True
                else:
                    # Non-success status code
                    log.warning(
                        "webhook_failed_status",
                        job_id=job_id,
                        status_code=response.status_code,
                        attempt=attempt,
                        response=response.text[:200]
                    )
                    
        except Exception as e:
            log.warning(
                "webhook_delivery_error",
                job_id=job_id,
                attempt=attempt,
                error=str(e)
            )
        
        # Wait before retry (exponential backoff: 2s, 4s, 8s)
        if attempt < max_retries:
            import asyncio
            wait_time = 2 ** attempt
            await asyncio.sleep(wait_time)
    
    # All retries failed
    duration = time.time() - start_time
    jobs.update_webhook_status(job_id, delivered=False, attempts=max_retries)
    
    # Track metrics
    from api.middleware.metrics import track_webhook_delivery
    track_webhook_delivery(success=False, duration_seconds=duration, retry_count=max_retries - 1)
    
    log.error("webhook_delivery_failed", job_id=job_id, max_retries=max_retries, duration=duration)
    return False
