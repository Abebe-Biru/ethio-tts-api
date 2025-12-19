"""
Rate limiting middleware using in-memory store
For production, use Redis or similar
"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
from typing import Dict, Tuple
import structlog

log = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware
    
    Tracks requests per IP/API key and enforces limits
    """
    
    def __init__(self, app, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        
        # Store: {identifier: [(timestamp, count), ...]}
        self.request_history: Dict[str, list] = defaultdict(list)
    
    def _get_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting (API key or IP)"""
        # Check for API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"key:{api_key}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _clean_old_requests(self, identifier: str, current_time: float):
        """Remove requests older than 1 hour"""
        if identifier in self.request_history:
            # Keep only requests from last hour
            self.request_history[identifier] = [
                (ts, count) for ts, count in self.request_history[identifier]
                if current_time - ts < 3600  # 1 hour
            ]
    
    def _check_rate_limit(self, identifier: str) -> Tuple[bool, dict]:
        """
        Check if request should be allowed
        
        Returns: (allowed, info_dict)
        """
        current_time = time.time()
        
        # Clean old requests
        self._clean_old_requests(identifier, current_time)
        
        # Count requests in last minute and hour
        requests_last_minute = sum(
            count for ts, count in self.request_history[identifier]
            if current_time - ts < 60
        )
        
        requests_last_hour = sum(
            count for ts, count in self.request_history[identifier]
        )
        
        # Check limits
        if requests_last_minute >= self.requests_per_minute:
            return False, {
                "limit": self.requests_per_minute,
                "window": "minute",
                "retry_after": 60,
                "current": requests_last_minute
            }
        
        if requests_last_hour >= self.requests_per_hour:
            return False, {
                "limit": self.requests_per_hour,
                "window": "hour",
                "retry_after": 3600,
                "current": requests_last_hour
            }
        
        return True, {
            "requests_last_minute": requests_last_minute,
            "requests_last_hour": requests_last_hour,
            "limit_per_minute": self.requests_per_minute,
            "limit_per_hour": self.requests_per_hour
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/v1/health", "/"]:
            return await call_next(request)
        
        identifier = self._get_identifier(request)
        current_time = time.time()
        
        # Check rate limit
        allowed, info = self._check_rate_limit(identifier)
        
        if not allowed:
            log.warning(
                "rate_limit_exceeded",
                identifier=identifier,
                limit=info["limit"],
                window=info["window"],
                current=info["current"]
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded: {info['limit']} requests per {info['window']}",
                    "limit": info["limit"],
                    "window": info["window"],
                    "retry_after_seconds": info["retry_after"]
                },
                headers={
                    "Retry-After": str(info["retry_after"]),
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": "0"
                }
            )
        
        # Record this request
        self.request_history[identifier].append((current_time, 1))
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            max(0, self.requests_per_minute - info["requests_last_minute"] - 1)
        )
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            max(0, self.requests_per_hour - info["requests_last_hour"] - 1)
        )
        
        return response
