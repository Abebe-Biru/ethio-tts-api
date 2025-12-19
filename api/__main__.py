#!/usr/bin/env python3
"""
Entry point for running the Oromo TTS API as a module.
Usage: python -m api
"""

if __name__ == "__main__":
    from .config import get_settings
    import uvicorn
    import os
    
    settings = get_settings()
    
    # Use PORT from environment (Railway sets this) or fall back to settings
    port = int(os.environ.get("PORT", settings.port))
    
    uvicorn.run(
        "api.main:app",  # Use string import for reload to work
        host=settings.host, 
        port=port, 
        reload=False  # Disable reload to avoid the warning
    )