"""
Audio File Storage Module

This module handles saving and serving audio files for async TTS jobs.
For MVP, we use local filesystem. Can be migrated to S3/Cloud Storage later.
"""

import os
import structlog
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import io

log = structlog.get_logger()

# ============================================================================
# STORAGE CONFIGURATION
# ============================================================================

class AudioStorage:
    """Audio file storage manager"""
    
    def __init__(self, storage_dir: str = "async_audio"):
        """
        Initialize storage manager.
        
        Args:
            storage_dir: Directory to store audio files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        log.info("audio_storage_initialized", storage_dir=str(self.storage_dir))
    
    async def save_audio(self, job_id: str, buffer: io.BytesIO) -> str:
        """
        Save audio file to storage.
        
        Args:
            job_id: Job identifier
            buffer: Audio data buffer
            
        Returns:
            File path where audio was saved
        """
        filename = f"{job_id}.wav"
        filepath = self.storage_dir / filename
        
        try:
            # Write buffer to file
            with open(filepath, 'wb') as f:
                f.write(buffer.getvalue())
            
            file_size = filepath.stat().st_size
            log.info("audio_saved", job_id=job_id, filepath=str(filepath), size_bytes=file_size)
            
            return str(filepath)
            
        except Exception as e:
            log.error("audio_save_failed", job_id=job_id, error=str(e))
            raise
    
    def get_audio_path(self, job_id: str) -> Optional[Path]:
        """
        Get path to audio file.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Path to audio file if exists, None otherwise
        """
        filename = f"{job_id}.wav"
        filepath = self.storage_dir / filename
        
        if filepath.exists():
            return filepath
        return None
    
    def delete_audio(self, job_id: str) -> bool:
        """
        Delete audio file.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if deleted, False if not found
        """
        filepath = self.get_audio_path(job_id)
        
        if filepath and filepath.exists():
            try:
                filepath.unlink()
                log.info("audio_deleted", job_id=job_id, filepath=str(filepath))
                return True
            except Exception as e:
                log.error("audio_delete_failed", job_id=job_id, error=str(e))
                return False
        
        return False
    
    async def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        Delete audio files older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of files deleted
        """
        now = datetime.now()
        cutoff_time = now - timedelta(hours=max_age_hours)
        deleted_count = 0
        
        try:
            for filepath in self.storage_dir.glob("*.wav"):
                # Get file modification time
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                
                if mtime < cutoff_time:
                    try:
                        filepath.unlink()
                        deleted_count += 1
                        log.debug("old_audio_deleted", filepath=str(filepath), age_hours=(now - mtime).total_seconds() / 3600)
                    except Exception as e:
                        log.error("cleanup_delete_failed", filepath=str(filepath), error=str(e))
            
            if deleted_count > 0:
                log.info("audio_cleanup_completed", deleted_count=deleted_count, max_age_hours=max_age_hours)
            
            return deleted_count
            
        except Exception as e:
            log.error("audio_cleanup_failed", error=str(e))
            return deleted_count
    
    def get_storage_stats(self) -> dict:
        """
        Get storage statistics.
        
        Returns:
            Dict with storage stats
        """
        try:
            files = list(self.storage_dir.glob("*.wav"))
            total_size = sum(f.stat().st_size for f in files)
            
            return {
                "total_files": len(files),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "storage_dir": str(self.storage_dir)
            }
        except Exception as e:
            log.error("storage_stats_failed", error=str(e))
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "storage_dir": str(self.storage_dir),
                "error": str(e)
            }


# ============================================================================
# GLOBAL STORAGE INSTANCE
# ============================================================================

# This will be initialized in main.py
_storage_instance: Optional[AudioStorage] = None


def get_storage() -> AudioStorage:
    """
    Get global storage instance.
    
    Returns:
        AudioStorage instance
    """
    global _storage_instance
    
    if _storage_instance is None:
        _storage_instance = AudioStorage()
    
    return _storage_instance


def init_storage(storage_dir: str = "async_audio") -> AudioStorage:
    """
    Initialize global storage instance.
    
    Args:
        storage_dir: Directory to store audio files
        
    Returns:
        AudioStorage instance
    """
    global _storage_instance
    _storage_instance = AudioStorage(storage_dir)
    return _storage_instance
