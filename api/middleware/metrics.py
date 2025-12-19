"""
Prometheus metrics for monitoring API performance

This module provides middleware and metrics collection for the TTS API.
Tracks requests, response times, cache performance, and errors.
"""
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import structlog
from typing import Callable

log = structlog.get_logger()

# ============================================================================
# METRICS DEFINITIONS
# ============================================================================

# Request metrics
request_count = Counter(
    "tts_api_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

request_duration = Histogram(
    "tts_api_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

# Cache metrics
cache_hits = Counter(
    "tts_cache_hits_total",
    "Total number of cache hits",
    ["language"]
)

cache_misses = Counter(
    "tts_cache_misses_total",
    "Total number of cache misses",
    ["language"]
)

# System metrics
active_requests = Gauge(
    "tts_api_active_requests",
    "Number of requests currently being processed"
)

# Error metrics
error_count = Counter(
    "tts_api_errors_total",
    "Total number of errors",
    ["error_type", "endpoint"]
)

# ============================================================================
# ASYNC JOB METRICS (Webhooks Feature)
# ============================================================================

# Job metrics
job_created_total = Counter(
    "tts_job_created_total",
    "Total number of async jobs created",
    ["language"]
)

job_status_total = Counter(
    "tts_job_status_total",
    "Total number of jobs by final status",
    ["status", "language"]
)

job_processing_duration = Histogram(
    "tts_job_processing_duration_seconds",
    "Job processing duration in seconds",
    ["language", "status"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
)

job_queue_length = Gauge(
    "tts_job_queue_length",
    "Current number of jobs in the queue"
)

job_pending_total = Gauge(
    "tts_job_pending_total",
    "Current number of pending jobs"
)

# Webhook metrics
webhook_delivery_total = Counter(
    "tts_webhook_delivery_total",
    "Total number of webhook delivery attempts",
    ["status"]  # success or failure
)

webhook_retry_total = Counter(
    "tts_webhook_retry_total",
    "Total number of webhook retry attempts"
)

webhook_delivery_duration = Histogram(
    "tts_webhook_delivery_duration_seconds",
    "Webhook delivery duration in seconds",
    ["status"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0)
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track request metrics for Prometheus
    
    Tracks:
    - Request count by method, endpoint, and status code
    - Request duration by method and endpoint
    - Active requests (gauge)
    - Error count by error type and endpoint
    
    The /metrics endpoint itself is excluded from tracking to avoid recursion.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and track metrics
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler
            
        Returns:
            Response: The HTTP response
        """
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        # Increment active requests
        active_requests.inc()
        start_time = time.time()
        
        status_code = 500  # Default to 500 in case of error
        
        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code
            
            # Calculate duration
            duration = time.time() - start_time

            # Track metrics
            request_count.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=status_code,
            ).inc()

            request_duration.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)

            return response

        except Exception as e:
            # Track error
            duration = time.time() - start_time
            
            error_count.labels(
                error_type=type(e).__name__,
                endpoint=request.url.path
            ).inc()
            
            # Still track the request (with error status)
            request_count.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=status_code,
            ).inc()
            
            request_duration.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            log.error(
                "request_error",
                method=request.method,
                endpoint=request.url.path,
                error_type=type(e).__name__,
                duration=duration
            )
            
            raise

        finally:
            # Always decrement active requests
            active_requests.dec()


# ============================================================================
# METRIC TRACKING FUNCTIONS
# ============================================================================

def track_job_created(language: str):
    """Track job creation"""
    job_created_total.labels(language=language).inc()


def track_job_completed(language: str, status: str, duration_seconds: float):
    """Track job completion"""
    job_status_total.labels(status=status, language=language).inc()
    job_processing_duration.labels(language=language, status=status).observe(duration_seconds)


def track_webhook_delivery(success: bool, duration_seconds: float, retry_count: int = 0):
    """Track webhook delivery"""
    status = "success" if success else "failure"
    webhook_delivery_total.labels(status=status).inc()
    webhook_delivery_duration.labels(status=status).observe(duration_seconds)
    
    if retry_count > 0:
        webhook_retry_total.inc(retry_count)


def update_queue_metrics(queue_length: int, pending_count: int):
    """Update queue metrics"""
    job_queue_length.set(queue_length)
    job_pending_total.set(pending_count)


def get_metrics() -> Response:
    """
    Generate Prometheus metrics in text format
    
    Returns:
        Response: HTTP response with Prometheus metrics
    """
    log.debug("metrics_requested")
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
