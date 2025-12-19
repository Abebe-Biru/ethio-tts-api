import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from transformers import VitsModel, AutoTokenizer
import io
import soundfile as sf
from tenacity import retry, stop_after_attempt, wait_exponential
import diskcache as dc
import hashlib
import anyio
from pyinstrument import Profiler
from boltons.iterutils import chunked
from tqdm.contrib.concurrent import thread_map
from pyrsistent import pmap
import structlog
import base64
from typing import List, Dict, Any, Tuple, Optional
from glom import glom

from .config import get_settings
from .models import TTSRequest, BatchTTSRequest, TokenizeRequest, HashRequest
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
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
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

# Global variables for models and cache
model_manager = None
cache = None

# Backward compatibility - keep these for legacy code
model = None
tokenizer = None
immutable_config = None

@app.on_event("startup")
async def startup_event():
    """Initialize models and cache on startup"""
    global model_manager, cache, model, tokenizer, immutable_config
    
    # Initialize diskcache
    cache = dc.Cache(settings.cache_dir)
    
    # Initialize multi-language model manager
    model_manager = MultiLanguageModelManager(settings.supported_languages)
    
    log.info(
        "startup_complete", 
        default_language=settings.default_language,
        supported_languages=list(settings.supported_languages.keys()),
        cache_dir=settings.cache_dir,
        note="Models will be loaded on first request (lazy loading)"
    )
    
    # Note: Models are NOT loaded during startup to avoid blocking the server
    # They will be loaded on-demand when first TTS request is made

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_waveform(inputs, model_instance):
    """Generate waveform with retry logic for transient failures."""
    with torch.no_grad():
        return model_instance(**inputs).waveform

async def get_model_for_language(language: str) -> Tuple[VitsModel, AutoTokenizer, dict]:
    """Get or load model for specified language"""
    global model, tokenizer, immutable_config
    
    # Check if model is already loaded
    model_instance, tokenizer_instance, config = model_manager.get_model(language)
    
    if model_instance is None:
        # Load model if not already loaded
        log.info("loading_model_for_request", language=language)
        model_instance, tokenizer_instance, config = await model_manager.load_model(language)
        
        # Update backward compatibility globals if this is the default language
        if language == settings.default_language:
            model = model_instance
            tokenizer = tokenizer_instance
            immutable_config = config
    
    return model_instance, tokenizer_instance, config

def sync_generate(text, language="oromo"):
    """Synchronous generation logic for offloading to thread."""
    # Get model for language (this will be called from thread, so we need the sync version)
    model_instance, tokenizer_instance, config = model_manager.get_model(language)
    
    if model_instance is None:
        raise RuntimeError(f"Model for language '{language}' is not loaded")
    
    # Use boltons for chunking if text is long
    words = text.split()
    if len(words) > 200:
        chunks = list(chunked(words, 200))
        processed_text = ' '.join([' '.join(chunk) for chunk in chunks])
        log.debug("text_chunked", original_len=len(words), chunks=len(chunks), language=language)
    else:
        processed_text = text
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    inputs = tokenizer_instance(processed_text, return_tensors="pt").to(device)
    output = generate_waveform(inputs, model_instance)
    waveform = output.squeeze().cpu().float().numpy()
    
    # Get sampling rate from config
    sampling_rate = glom(config, 'sampling_rate', default=16000)
    
    buffer = io.BytesIO()
    sf.write(buffer, waveform, sampling_rate, format="WAV")
    buffer.seek(0)
    return buffer

def process_single_text(text, language="oromo"):
    """Wrapper for thread_map in batch processing."""
    buffer = sync_generate(text, language)
    # Include language in cache key for language-specific caching
    text_hash = hashlib.md5(f"{language}:{text}".encode()).hexdigest()
    cache_key = f"waveform_{language}_{text_hash}"
    waveform_bytes = buffer.getvalue()
    cache[cache_key] = waveform_bytes
    return {"hash": text_hash, "audio_b64": base64.b64encode(waveform_bytes).decode('utf-8')}

def get_cached_items(language: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get list of cached items with metadata, optionally filtered by language.
    
    Args:
        language: Optional language code to filter by
    
    Returns:
        List of cached items with details
    """
    if not cache:
        raise RuntimeError("Cache not initialized")
    
    cached_items = []
    
    for key in cache:
        if key.startswith("waveform_"):
            parts = key.split("_")
            if len(parts) >= 3:
                lang = parts[1]
                hash_value = parts[2]
                
                # Filter by language if specified
                if language is not None and lang != language:
                    continue
                
                try:
                    size_bytes = len(cache[key])
                    cached_items.append({
                        "language": lang,
                        "hash": hash_value,
                        "cache_key": key,
                        "size_bytes": size_bytes,
                        "size_kb": round(size_bytes / 1024, 2)
                    })
                except:
                    pass
    
    # Sort by language, then by hash
    cached_items.sort(key=lambda x: (x["language"], x["hash"]))
    
    return cached_items

def clear_cache_by_language(language: Optional[str] = None) -> Dict[str, Any]:
    """
    Clear cache for specific language or all languages.
    
    Args:
        language: Language code to clear cache for, or None to clear all
        
    Returns:
        Dictionary with clearing statistics
    """
    if not cache:
        raise RuntimeError("Cache not initialized")
    
    items_cleared = 0
    size_freed = 0
    languages_affected = set()
    
    # Collect keys to delete
    keys_to_delete = []
    for key in cache:
        if key.startswith("waveform_"):
            parts = key.split("_")
            if len(parts) >= 2:
                lang = parts[1]
                
                # If language specified, only clear that language
                if language is None or lang == language:
                    keys_to_delete.append(key)
                    languages_affected.add(lang)
                    try:
                        size_freed += len(cache[key])
                    except:
                        pass
    
    # Delete keys
    for key in keys_to_delete:
        del cache[key]
        items_cleared += 1
    
    return {
        "items_cleared": items_cleared,
        "size_freed_mb": round(size_freed / (1024 * 1024), 2),
        "languages_affected": sorted(list(languages_affected))
    }

def clear_specific_cache_item(language: str, hash_value: str) -> Dict[str, Any]:
    """
    Clear specific cached item by language and hash.
    
    Args:
        language: Language code
        hash_value: Hash of the cached item
        
    Returns:
        Dictionary with clearing statistics
    """
    if not cache:
        raise RuntimeError("Cache not initialized")
    
    cache_key = f"waveform_{language}_{hash_value}"
    
    if cache_key not in cache:
        raise KeyError(f"Cache item not found: {cache_key}")
    
    # Get size before deleting
    size_freed = len(cache[cache_key])
    
    # Delete the item
    del cache[cache_key]
    
    return {
        "cache_key": cache_key,
        "language": language,
        "hash": hash_value,
        "size_freed_kb": round(size_freed / 1024, 2)
    }


# ============================================================================
# API ENDPOINTS - Ordered by recommended workflow
# ============================================================================

# 1. HEALTH CHECK - Check if API is running
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    loaded_languages = model_manager.get_loaded_languages() if model_manager else []
    supported_languages = list(settings.supported_languages.keys())
    
    return {
        "status": "healthy",
        "model_loaded": len(loaded_languages) > 0,  # At least one model loaded
        "cache_size": len(cache) if cache else 0,
        "supported_languages": supported_languages,
        "loaded_languages": loaded_languages,
        "default_language": settings.default_language
    }


# 2. GET LANGUAGES - Check available languages
@app.get("/languages")
async def get_languages():
    """Get supported languages and their status"""
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


# 3. LOAD MODEL - Load model for specific language
@app.post("/languages/{language}/load")
async def load_language_model(language: str):
    """Load model for specific language"""
    if not model_manager:
        raise HTTPException(status_code=500, detail="Model manager not initialized")
    
    try:
        if language not in settings.supported_languages:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported language '{language}'. Supported: {list(settings.supported_languages.keys())}"
            )
        
        if model_manager.is_model_loaded(language):
            return {"message": f"Model for '{language}' is already loaded"}
        
        await model_manager.load_model(language)
        return {"message": f"Model for '{language}' loaded successfully"}
        
    except Exception as e:
        log.error("manual_model_load_failed", language=language, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")


# 4. GENERATE SPEECH - Convert single text to speech
@app.post("/tts")
async def generate_speech(request: TTSRequest):
    """Generate speech from text"""
    if not request.text.strip():
        log.warning("empty_text_request")
        raise HTTPException(status_code=400, detail="Text input cannot be empty")
    
    language = request.language or settings.default_language
    log.info("tts_request_received", text_length=len(request.text), language=language)
    
    try:
        # Ensure model is loaded for the requested language
        await get_model_for_language(language)
        
        # Include language in cache key for language-specific caching
        text_hash = hashlib.md5(f"{language}:{request.text}".encode()).hexdigest()
        cache_key = f"waveform_{language}_{text_hash}"
        
        # Check cache first
        if cache_key in cache:
            waveform_bytes = cache[cache_key]
            log.info("cache_hit", cache_key=cache_key, language=language)
            
            # Dynamic filename based on language
            filename = f"{language}_speech.wav"
            return StreamingResponse(
                io.BytesIO(waveform_bytes),
                media_type="audio/wav",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        # Generate new audio
        if settings.debug:
            profiler = Profiler()
            profiler.start()
        
        buffer = await anyio.to_thread.run_sync(sync_generate, request.text, language)
        
        if settings.debug:
            profiler.stop()
            print(profiler.output_text(unicode=True, color=True))
        
        # Cache the result
        waveform_bytes = buffer.getvalue()
        cache[cache_key] = waveform_bytes
        
        log.info("tts_generated", text_length=len(request.text), language=language)
        
        # Dynamic filename based on language
        filename = f"{language}_speech.wav"
        return StreamingResponse(
            buffer,
            media_type="audio/wav",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        log.error("tts_generation_failed", error=str(e), text_length=len(request.text), language=language)
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")


# 5. BATCH GENERATION - Convert multiple texts to speech
@app.post("/batch_tts")
async def generate_batch_speech(request: BatchTTSRequest):
    """Generate speech for multiple texts"""
    if not request.texts:
        log.warning("empty_batch_request")
        raise HTTPException(status_code=400, detail="Texts list cannot be empty")
    
    language = request.language or settings.default_language
    log.info("batch_tts_request_received", num_texts=len(request.texts), language=language)
    
    try:
        # Ensure model is loaded for the requested language
        await get_model_for_language(language)
        
        # Check cache for each text
        cached_results = []
        to_process = []
        
        for text in request.texts:
            # Include language in cache key
            text_hash = hashlib.md5(f"{language}:{text}".encode()).hexdigest()
            cache_key = f"waveform_{language}_{text_hash}"
            if cache_key in cache:
                waveform_bytes = cache[cache_key]
                cached_results.append({
                    "hash": text_hash, 
                    "audio_b64": base64.b64encode(waveform_bytes).decode('utf-8')
                })
                log.debug("batch_cache_hit", cache_key=cache_key, language=language)
            else:
                to_process.append(text)
        
        # Process uncached texts
        if to_process:
            if settings.debug:
                profiler = Profiler()
                profiler.start()
            
            def run_batch():
                return thread_map(
                    lambda text: process_single_text(text, language),
                    to_process, 
                    max_workers=4, 
                    disable=(not settings.debug)
                )
            
            new_results = await anyio.to_thread.run_sync(run_batch)
            
            if settings.debug:
                profiler.stop()
                print(profiler.output_text(unicode=True, color=True))
            
            cached_results.extend(new_results)
            log.info("batch_generated", num_new=len(to_process), language=language)
        
        return JSONResponse(content={"results": cached_results})
        
    except Exception as e:
        log.error("batch_tts_failed", error=str(e), num_texts=len(request.texts), language=language)
        raise HTTPException(status_code=500, detail=f"Error generating batch speech: {str(e)}")


# 6. ROOT - API information
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Multi-Language TTS API is running!",
        "version": "2.0.0",
        "api_versions": ["v1", "legacy"],
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
            "v1_health": "GET /v1/health - Health check (v1)",
            "v1_languages": "GET /v1/languages - List languages (v1)",
            "v1_load_model": "POST /v1/languages/{language}/load - Load model (v1)",
            "v1_tts": "POST /v1/tts - Generate speech (v1)",
            "v1_batch_tts": "POST /v1/batch_tts - Batch generation (v1)",
            "metrics": "GET /metrics - Prometheus metrics",
            "health": "GET /health - Health check (legacy)",
            "languages": "GET /languages - Get supported languages (legacy)",
            "load_model": "POST /languages/{language}/load - Load model (legacy)",
            "tts": "POST /tts - Convert text to speech (legacy)",
            "batch_tts": "POST /batch_tts - Batch conversion (legacy)",
            "docs": "GET /docs - API documentation (debug mode only)"
        },
        "rate_limits": {
            "per_minute": 60,
            "per_hour": 1000,
            "note": "Use X-API-Key header for higher limits"
        }
    }


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return get_metrics()


# 7. DEBUG ENDPOINTS - Only available in debug mode

@app.post("/debug/tokenize")
async def debug_tokenize(request: TokenizeRequest):
    """Debug endpoint to see how text gets tokenized for different languages"""
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Debug endpoint only available in DEBUG mode")
    
    try:
        language = request.language or settings.default_language
        
        # Ensure model is loaded
        model_instance, tokenizer_instance, config = await get_model_for_language(language)
        
        # Tokenize the text
        inputs = tokenizer_instance(request.text, return_tensors="pt")
        
        # Get token IDs and decode them back
        token_ids = inputs['input_ids'][0].tolist()
        tokens = [tokenizer_instance.decode([tid]) for tid in token_ids]
        
        # Get vocabulary info
        vocab_size = len(tokenizer_instance.get_vocab())
        
        log.info("debug_tokenize_executed", language=language, num_tokens=len(token_ids))
        
        return {
            "text": request.text,
            "language": language,
            "token_count": len(token_ids),
            "token_ids": token_ids,
            "tokens": tokens,
            "vocab_size": vocab_size,
            "tokenizer_class": tokenizer_instance.__class__.__name__
        }
        
    except Exception as e:
        log.error("debug_tokenize_failed", error=str(e), language=request.language)
        raise HTTPException(status_code=500, detail=f"Tokenization failed: {str(e)}")


@app.get("/debug/model-info")
async def debug_model_info(language: Optional[str] = None):
    """Debug endpoint to get detailed model configuration"""
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Debug endpoint only available in DEBUG mode")
    
    try:
        target_language = language or settings.default_language
        
        # Ensure model is loaded
        model_instance, tokenizer_instance, config = await get_model_for_language(target_language)
        
        # Get model info
        device = next(model_instance.parameters()).device
        dtype = next(model_instance.parameters()).dtype
        
        # Count parameters
        total_params = sum(p.numel() for p in model_instance.parameters())
        trainable_params = sum(p.numel() for p in model_instance.parameters() if p.requires_grad)
        
        # Get model architecture info
        model_config = {
            "sampling_rate": glom(config, 'sampling_rate', default=16000),
            "hidden_size": getattr(config, 'hidden_size', None),
            "num_hidden_layers": getattr(config, 'num_hidden_layers', None),
            "num_attention_heads": getattr(config, 'num_attention_heads', None),
            "vocab_size": getattr(config, 'vocab_size', None),
        }
        
        log.info("debug_model_info_executed", language=target_language)
        
        return {
            "language": target_language,
            "model_name": settings.supported_languages.get(target_language),
            "device": str(device),
            "dtype": str(dtype),
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "parameters_in_millions": round(total_params / 1_000_000, 2),
            "model_config": model_config,
            "model_class": model_instance.__class__.__name__,
            "tokenizer_class": tokenizer_instance.__class__.__name__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0
        }
        
    except Exception as e:
        log.error("debug_model_info_failed", error=str(e), language=language)
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")


@app.get("/debug/cache-stats")
async def debug_cache_stats():
    """Debug endpoint to see cache statistics"""
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Debug endpoint only available in DEBUG mode")
    
    try:
        if not cache:
            return {"error": "Cache not initialized"}
        
        # Get cache statistics
        cache_size = len(cache)
        
        # Analyze cache contents
        language_stats = {}
        total_size_bytes = 0
        
        for key in cache:
            if key.startswith("waveform_"):
                # Extract language from key: waveform_{lang}_{hash}
                parts = key.split("_")
                if len(parts) >= 2:
                    lang = parts[1]
                    if lang not in language_stats:
                        language_stats[lang] = {"count": 0, "size_bytes": 0}
                    
                    language_stats[lang]["count"] += 1
                    
                    # Get size of cached item
                    try:
                        item_size = len(cache[key])
                        language_stats[lang]["size_bytes"] += item_size
                        total_size_bytes += item_size
                    except:
                        pass
        
        # Convert bytes to MB
        for lang in language_stats:
            language_stats[lang]["size_mb"] = round(language_stats[lang]["size_bytes"] / (1024 * 1024), 2)
        
        log.info("debug_cache_stats_executed", cache_size=cache_size)
        
        return {
            "cache_enabled": True,
            "cache_directory": settings.cache_dir,
            "total_cached_items": cache_size,
            "total_size_bytes": total_size_bytes,
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
            "language_breakdown": language_stats,
            "cache_hits_available": "Use structlog output to see cache hit/miss logs"
        }
        
    except Exception as e:
        log.error("debug_cache_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@app.get("/cache")
async def get_all_cache_items():
    """Get list of all cached items with metadata"""
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Cache access only available in DEBUG mode")
    
    try:
        items = get_cached_items()
        
        # Calculate summary stats
        total_size_bytes = sum(item["size_bytes"] for item in items)
        languages = list(set(item["language"] for item in items))
        
        log.info("cache_items_retrieved", count=len(items))
        
        return {
            "total_items": len(items),
            "total_size_kb": round(total_size_bytes / 1024, 2),
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
            "languages": sorted(languages),
            "items": items
        }
        
    except Exception as e:
        log.error("cache_items_retrieval_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cache items: {str(e)}")


@app.delete("/cache")
async def clear_all_cache():
    """Clear entire cache - removes all cached audio files"""
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Cache clearing only available in DEBUG mode")
    
    try:
        result = clear_cache_by_language(None)
        
        log.info(
            "cache_cleared_all",
            items_cleared=result["items_cleared"],
            size_freed_mb=result["size_freed_mb"],
            languages_affected=result["languages_affected"]
        )
        
        return {
            "message": "Cache cleared successfully",
            "items_cleared": result["items_cleared"],
            "size_freed_mb": result["size_freed_mb"],
            "languages_affected": result["languages_affected"]
        }
        
    except Exception as e:
        log.error("cache_clear_all_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@app.get("/cache/{language}")
async def get_language_cache_items(language: str):
    """Get list of cached items for specific language"""
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Cache access only available in DEBUG mode")
    
    try:
        # Validate language
        if language not in settings.supported_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language '{language}'. Supported: {list(settings.supported_languages.keys())}"
            )
        
        items = get_cached_items(language)
        
        # Calculate summary stats
        total_size_bytes = sum(item["size_bytes"] for item in items)
        
        log.info("cache_items_retrieved_language", language=language, count=len(items))
        
        return {
            "language": language,
            "total_items": len(items),
            "total_size_kb": round(total_size_bytes / 1024, 2),
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
            "items": items
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error("cache_items_retrieval_failed", language=language, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cache items for language '{language}': {str(e)}")


@app.delete("/cache/{language}")
async def clear_language_cache(language: str):
    """Clear cache for specific language only"""
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Cache clearing only available in DEBUG mode")
    
    try:
        # Validate language
        if language not in settings.supported_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language '{language}'. Supported: {list(settings.supported_languages.keys())}"
            )
        
        result = clear_cache_by_language(language)
        
        log.info(
            "cache_cleared_language",
            language=language,
            items_cleared=result["items_cleared"],
            size_freed_mb=result["size_freed_mb"]
        )
        
        return {
            "message": f"Cache cleared for language '{language}'",
            "language": language,
            "items_cleared": result["items_cleared"],
            "size_freed_mb": result["size_freed_mb"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error("cache_clear_language_failed", language=language, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to clear cache for language '{language}': {str(e)}")


@app.get("/cache/{language}/{hash}")
async def get_cached_audio(language: str, hash: str):
    """Get cached audio file by language and hash"""
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Cache access only available in DEBUG mode")
    
    try:
        # Validate language
        if language not in settings.supported_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language '{language}'. Supported: {list(settings.supported_languages.keys())}"
            )
        
        cache_key = f"waveform_{language}_{hash}"
        
        # Check if item exists in cache
        if cache_key not in cache:
            raise HTTPException(
                status_code=404,
                detail=f"Cached audio not found for hash '{hash}' in language '{language}'"
            )
        
        # Get cached audio
        waveform_bytes = cache[cache_key]
        
        log.info("cached_audio_retrieved", language=language, hash=hash, size_bytes=len(waveform_bytes))
        
        # Return audio file
        filename = f"{language}_{hash}.wav"
        return StreamingResponse(
            io.BytesIO(waveform_bytes),
            media_type="audio/wav",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.error("cached_audio_retrieval_failed", language=language, hash=hash, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cached audio: {str(e)}")


@app.delete("/cache/{language}/{hash}")
async def clear_specific_cache(language: str, hash: str):
    """Clear specific cached item by language and hash"""
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Cache clearing only available in DEBUG mode")
    
    try:
        # Validate language
        if language not in settings.supported_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language '{language}'. Supported: {list(settings.supported_languages.keys())}"
            )
        
        result = clear_specific_cache_item(language, hash)
        
        log.info(
            "cache_cleared_specific",
            language=language,
            hash=hash,
            size_freed_kb=result["size_freed_kb"]
        )
        
        return {
            "message": f"Cache item cleared successfully",
            "cache_key": result["cache_key"],
            "language": result["language"],
            "hash": result["hash"],
            "size_freed_kb": result["size_freed_kb"]
        }
        
    except KeyError as e:
        log.warning("cache_item_not_found", language=language, hash=hash)
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        log.error("cache_clear_specific_failed", language=language, hash=hash, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to clear cache item: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port, reload=True)