"""
API Key authentication and management
"""
from fastapi import Request, HTTPException, Header
from typing import Optional, Dict
import secrets
import hashlib
import time
import structlog

log = structlog.get_logger()


class APIKeyManager:
    """
    Simple API key manager
    
    For production, use a database
    """
    
    def __init__(self):
        # Store: {api_key_hash: {user_id, created_at, name, active}}
        self.keys: Dict[str, dict] = {}
        
        # Create a default demo key
        demo_key = "demo_key_12345"
        self.keys[self._hash_key(demo_key)] = {
            "user_id": "demo_user",
            "created_at": time.time(),
            "name": "Demo Key",
            "active": True,
            "tier": "free"
        }
        
        log.info("api_key_manager_initialized", demo_key=demo_key)
    
    def _hash_key(self, key: str) -> str:
        """Hash API key for storage"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def generate_key(self, user_id: str, name: str = "API Key", tier: str = "free") -> str:
        """Generate new API key"""
        # Generate secure random key
        key = f"sk_{secrets.token_urlsafe(32)}"
        key_hash = self._hash_key(key)
        
        # Store key info
        self.keys[key_hash] = {
            "user_id": user_id,
            "created_at": time.time(),
            "name": name,
            "active": True,
            "tier": tier
        }
        
        log.info("api_key_generated", user_id=user_id, name=name)
        
        return key
    
    def validate_key(self, key: str) -> Optional[dict]:
        """
        Validate API key
        
        Returns key info if valid, None otherwise
        """
        if not key:
            return None
        
        key_hash = self._hash_key(key)
        
        if key_hash not in self.keys:
            log.warning("invalid_api_key_attempt", key_prefix=key[:10])
            return None
        
        key_info = self.keys[key_hash]
        
        if not key_info.get("active", False):
            log.warning("inactive_api_key_attempt", user_id=key_info.get("user_id"))
            return None
        
        return key_info
    
    def revoke_key(self, key: str) -> bool:
        """Revoke API key"""
        key_hash = self._hash_key(key)
        
        if key_hash in self.keys:
            self.keys[key_hash]["active"] = False
            log.info("api_key_revoked", user_id=self.keys[key_hash].get("user_id"))
            return True
        
        return False
    
    def list_keys(self, user_id: str) -> list:
        """List all keys for a user"""
        return [
            {
                "name": info["name"],
                "created_at": info["created_at"],
                "active": info["active"],
                "tier": info.get("tier", "free")
            }
            for key_hash, info in self.keys.items()
            if info["user_id"] == user_id
        ]


# Global API key manager instance
api_key_manager = APIKeyManager()


def get_api_key_manager() -> APIKeyManager:
    """Get API key manager instance"""
    return api_key_manager


async def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> Optional[dict]:
    """
    Dependency to verify API key
    
    Returns key info if valid, None if no key provided
    Raises HTTPException if key is invalid
    """
    if not x_api_key:
        # No key provided - allow for now (optional auth)
        return None
    
    key_info = api_key_manager.validate_key(x_api_key)
    
    if not key_info:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "invalid_api_key",
                "message": "Invalid or inactive API key"
            },
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    return key_info
