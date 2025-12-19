#!/usr/bin/env python3
"""
Simple entry point for Railway deployment
"""
import os
import uvicorn

if __name__ == "__main__":
    # Get port from environment (Railway sets this)
    port = int(os.environ.get("PORT", 8001))
    host = os.environ.get("HOST", "0.0.0.0")
    
    # Run the app
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=False
    )
