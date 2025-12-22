"""
Multi-Language TTS API - Clean v1-only version
"""
import structlog
import diskcache as dc
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .model_manager import MultiLanguageModelManager
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.metrics import MetricsMiddleware, get_metrics
from .v1 import routes as v1_routes

# Setup structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
log = structlog.get_logger()

# Get settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Language TTS API",
    description="A FastAPI service for text-to-speech in Oromo and Amharic using Meta's MMS-TTS models",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middlewares (order matters!)
# 1. CORS - must be first
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# 2. Metrics tracking
app.add_middleware(MetricsMiddleware)

# 3. Rate limiting
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    requests_per_hour=1000
)

# Include v1 routes
app.include_router(v1_routes.router)

# Global variables for models and cache (accessible by v1 routes)
model_manager = None
cache = None
storage = None


@app.on_event("startup")
async def startup_event():
    """Initialize models, cache, storage, and background worker on startup"""
    global model_manager, cache, storage
    
    # Initialize diskcache
    cache = dc.Cache(settings.cache_dir)
    
    # Initialize multi-language model manager
    model_manager = MultiLanguageModelManager(settings.supported_languages)
    
    # Initialize audio storage
    from .storage import init_storage
    storage = init_storage("async_audio")
    
    # Start background worker
    from .workers import start_worker
    start_worker(model_manager, cache, storage)
    
    log.info(
        "startup_complete", 
        default_language=settings.default_language,
        supported_languages=list(settings.supported_languages.keys()),
        cache_dir=settings.cache_dir,
        storage_dir="async_audio",
        background_worker="started",
        note="Models will be loaded on first request (lazy loading)"
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    from .workers import stop_worker
    stop_worker()
    log.info("shutdown_complete", background_worker="stopped")


# ============================================================================
# CORE ENDPOINTS - Root and Metrics only
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint with information"""
    return {
        "message": "Multi-Language TTS API",
        "version": "2.0.0",
        "api_version": "v1",
        "supported_languages": list(settings.supported_languages.keys()),
        "default_language": settings.default_language,
        "features": [
            "Multi-language TTS (Oromo, Amharic)",
            "Rate limiting (60/min, 1000/hour)",
            "API key authentication",
            "Prometheus metrics",
            "Audio caching",
            "Batch processing"
        ],
        "endpoints": {
            "health": "GET /v1/health - Health check",
            "languages": "GET /v1/languages - List supported languages",
            "load_model": "POST /v1/languages/{language}/load - Preload language model",
            "tts": "POST /v1/tts - Generate speech from text",
            "batch_tts": "POST /v1/batch_tts - Batch speech generation",
            "metrics": "GET /metrics - Prometheus metrics",
            "docs": "GET /docs - API documentation (debug mode only)"
        },
        "rate_limits": {
            "per_minute": 60,
            "per_hour": 1000,
            "note": "Use X-API-Key header for tracking"
        },
        "documentation": {
            "quick_start": "See QUICK_START_V1.md",
            "full_guide": "See API_V1_GUIDE.md",
            "upgrade_info": "See UPGRADE_SUMMARY.md"
        }
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return get_metrics()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port, reload=True)
