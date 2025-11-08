"""
Persistent caching system for market data and related information.
Handles saving and loading of market data to/from JSON files.
"""

import os
import json
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
from ..utils.logger import logger

class MarketCache:
    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize the market cache with a specified cache directory.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_cache_path(self, filename: str) -> Path:
        """Get the full path for a cache file."""
        return self.cache_dir / filename
        
    def save_data(self, filename: str, data: Any) -> None:
        """
        Save data to a JSON cache file.
        
        Args:
            filename: Name of the cache file
            data: Data to cache (must be JSON serializable)
        """
        try:
            cache_path = self._get_cache_path(filename)
            
            # Ensure the cache directory exists
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Add metadata to cached data
            cache_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            with cache_path.open('w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.debug(f"Saved cache file: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to save cache file {filename}: {e}")
            raise
            
    def load_data(self, filename: str, max_age_hours: float = 24.0) -> Any:
        """
        Load data from a JSON cache file if it exists and is not too old.
        
        Args:
            filename: Name of the cache file
            max_age_hours: Maximum age of cache in hours (default: 24)
            
        Returns:
            Cached data if valid, None otherwise
        """
        try:
            cache_path = self._get_cache_path(filename)
            
            if not cache_path.exists():
                return None
                
            with cache_path.open('r') as f:
                cache_data = json.load(f)
                
            # Check cache age
            timestamp = datetime.fromisoformat(cache_data["timestamp"])
            age = (datetime.utcnow() - timestamp).total_seconds() / 3600
            
            if age > max_age_hours:
                logger.debug(f"Cache file {filename} is too old ({age:.1f} hours)")
                return None
                
            return cache_data["data"]
            
        except Exception as e:
            logger.error(f"Failed to load cache file {filename}: {e}")
            return None
            
    def clear_cache(self, filename: str = None) -> None:
        """
        Clear specific cache file or all cache files.
        
        Args:
            filename: Specific file to clear, or None to clear all
        """
        try:
            if filename:
                cache_path = self._get_cache_path(filename)
                if cache_path.exists():
                    cache_path.unlink()
                    logger.debug(f"Cleared cache file: {filename}")
            else:
                # Clear all .json files in cache directory
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink()
                logger.debug("Cleared all cache files")
                    
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            raise

# Initialize global cache instance
cache = MarketCache()