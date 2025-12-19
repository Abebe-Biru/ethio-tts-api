import os
from functools import lru_cache
from typing import List, Dict
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings"""
    
    # Model configuration (backward compatibility)
    model_name: str = "facebook/mms-tts-orm"
    
    # Multi-language model configuration
    supported_languages: Dict[str, str] = {
        "oromo": "facebook/mms-tts-orm",
        "amharic": "facebook/mms-tts-amh",
        "om": "facebook/mms-tts-orm",  # ISO code alias
        "am": "facebook/mms-tts-amh"  # ISO code alias
    }
    
    # Default language
    default_language: str = "oromo"
    
    # Cache configuration
    cache_dir: str = "tts_cache"
    
    # Debug mode
    debug: bool = False
    
    # CORS configuration (as string, will be parsed)
    cors_origins_str: str = Field(default="*", alias="CORS_ORIGINS")
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8001
    
    # Webhook configuration
    webhook_secret: str = Field(
        default="your-webhook-secret-key-change-in-production",
        description="Secret key for webhook HMAC signature generation"
    )
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from string"""
        if self.cors_origins_str == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins_str.split(',')]
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "populate_by_name": True
    }

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()