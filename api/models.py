from pydantic import BaseModel, Field, validator, HttpUrl
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class TTSRequest(BaseModel):
    """Request model for single text-to-speech conversion"""
    text: str = Field(..., min_length=1, max_length=10000, description="Text to convert to speech")
    language: Optional[str] = Field(
        default="oromo", 
        description="Language for TTS generation. Supported: 'oromo', 'amharic', 'om', 'am'"
    )
    
    @validator('language')
    def validate_language(cls, v):
        if v is None:
            return "oromo"
        v = v.lower().strip()
        supported = {"oromo", "amharic", "om", "am"}
        if v not in supported:
            raise ValueError(f"Unsupported language '{v}'. Supported languages: {', '.join(supported)}")
        return v

class BatchTTSRequest(BaseModel):
    """Request model for batch text-to-speech conversion"""
    texts: List[str] = Field(..., min_items=1, max_items=100, description="List of texts to convert to speech")
    language: Optional[str] = Field(
        default="oromo", 
        description="Language for TTS generation. Supported: 'oromo', 'amharic', 'om', 'am'"
    )
    
    @validator('language')
    def validate_language(cls, v):
        if v is None:
            return "oromo"
        v = v.lower().strip()
        supported = {"oromo", "amharic", "om", "am"}
        if v not in supported:
            raise ValueError(f"Unsupported language '{v}'. Supported languages: {', '.join(supported)}")
        return v

class TokenizeRequest(BaseModel):
    """Request model for tokenization debug"""
    text: str = Field(..., min_length=1, description="Text to tokenize")
    language: Optional[str] = Field(default="orm", description="Language for tokenization")
    
    @validator('language')
    def validate_language(cls, v):
        if v is None:
            return "orm"
        return v.lower().strip()

class HashRequest(BaseModel):
    """Request model for hash calculation"""
    text: str = Field(..., min_length=1, description="Text to calculate hash for")
    language: Optional[str] = Field(default="orm", description="Language for hash calculation")
    
    @validator('language')
    def validate_language(cls, v):
        if v is None:
            return "orm"
        return v.lower().strip()

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    model_loaded: bool
    cache_size: int

class TTSResponse(BaseModel):
    """Response model for TTS operations"""
    message: str
    audio_url: str = None

class BatchTTSResponse(BaseModel):
    """Response model for batch TTS operations"""
    results: List[Dict[str, str]]

# ============================================================================
# ASYNC JOB MODELS (Webhooks Feature)
# ============================================================================

class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AsyncTTSRequest(BaseModel):
    """Request model for async TTS job creation"""
    text: str = Field(..., min_length=1, max_length=50000, description="Text to convert to speech")
    language: Optional[str] = Field(
        default="oromo",
        description="Language for TTS generation. Supported: 'oromo', 'amharic', 'om', 'am'"
    )
    webhook_url: HttpUrl = Field(..., description="URL to receive webhook notification when job completes")
    
    @validator('language')
    def validate_language(cls, v):
        if v is None:
            return "oromo"
        v = v.lower().strip()
        supported = {"oromo", "amharic", "om", "am"}
        if v not in supported:
            raise ValueError(f"Unsupported language '{v}'. Supported languages: {', '.join(supported)}")
        return v

class Job(BaseModel):
    """Job data model for async TTS processing"""
    job_id: str = Field(..., description="Unique job identifier (UUID)")
    text: str = Field(..., description="Text to convert to speech")
    language: str = Field(..., description="Language for TTS generation")
    webhook_url: str = Field(..., description="URL to receive webhook notification")
    status: JobStatus = Field(default=JobStatus.PENDING, description="Current job status")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job processing start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    audio_url: Optional[str] = Field(None, description="URL to download generated audio")
    error_message: Optional[str] = Field(None, description="Error message if job failed")
    webhook_delivered: bool = Field(default=False, description="Whether webhook was successfully delivered")
    webhook_attempts: int = Field(default=0, description="Number of webhook delivery attempts")
    
    class Config:
        use_enum_values = True

class JobResponse(BaseModel):
    """Response model for job status queries"""
    job_id: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    audio_url: Optional[str] = None
    error_message: Optional[str] = None

class JobCreateResponse(BaseModel):
    """Response model for job creation"""
    job_id: str
    status: str
    message: str
    created_at: datetime

class JobListResponse(BaseModel):
    """Response model for listing jobs"""
    jobs: List[JobResponse]
    total: int
    page: int
    page_size: int