"""
Caching mechanisms for improved performance
"""
import asyncio
import time
import logging
from typing import Any, Dict, Optional, Callable, Union
import hashlib
import json
import pickle
from pathlib import Path
import threading
from functools import wraps

logger = logging.getLogger(__name__)

class MemoryCache:
    """
    Thread-safe in-memory cache with TTL support
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.RLock()
        
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments"""
        key_data = {
            'args': args,
            'kwargs': kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if current_time > entry['expires']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            self._access_times.pop(key, None)
    
    def _evict_lru(self):
        """Evict least recently used entries if cache is full"""
        if len(self._cache) >= self.max_size:
            # Find least recently used key
            lru_key = min(self._access_times.keys(), key=lambda k: self._access_times[k])
            del self._cache[lru_key]
            del self._access_times[lru_key]
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            self._cleanup_expired()
            
            if key in self._cache:
                entry = self._cache[key]
                if time.time() <= entry['expires']:
                    self._access_times[key] = time.time()
                    return entry['value']
                else:
                    del self._cache[key]
                    self._access_times.pop(key, None)
            
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        with self._lock:
            self._cleanup_expired()
            self._evict_lru()
            
            ttl = ttl or self.default_ttl
            expires = time.time() + ttl
            
            self._cache[key] = {
                'value': value,
                'expires': expires
            }
            self._access_times[key] = time.time()
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._access_times.pop(key, None)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            self._cleanup_expired()
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate': getattr(self, '_hits', 0) / max(getattr(self, '_requests', 1), 1)
            }

class AsyncMemoryCache(MemoryCache):
    """
    Async version of memory cache
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        super().__init__(max_size, default_ttl)
        self._async_lock = asyncio.Lock()
    
    async def aget(self, key: str) -> Optional[Any]:
        """Async get value from cache"""
        async with self._async_lock:
            return self.get(key)
    
    async def aset(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Async set value in cache"""
        async with self._async_lock:
            self.set(key, value, ttl)
    
    async def adelete(self, key: str) -> bool:
        """Async delete key from cache"""
        async with self._async_lock:
            return self.delete(key)

class FileCache:
    """
    File-based cache for persistent storage
    """
    
    def __init__(self, cache_dir: str = "cache", max_file_size: int = 50 * 1024 * 1024):  # 50MB
        self.cache_dir = Path(cache_dir)
        self.max_file_size = max_file_size
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key"""
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.cache"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from file cache"""
        try:
            file_path = self._get_file_path(key)
            if not file_path.exists():
                return None
            
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            
            # Check if expired
            if time.time() > data['expires']:
                file_path.unlink(missing_ok=True)
                return None
            
            return data['value']
            
        except Exception as e:
            logger.error(f"Error reading from file cache: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in file cache"""
        try:
            file_path = self._get_file_path(key)
            expires = time.time() + ttl
            
            data = {
                'value': value,
                'expires': expires,
                'created': time.time()
            }
            
            # Check size before writing
            serialized = pickle.dumps(data)
            if len(serialized) > self.max_file_size:
                logger.warning(f"Cache value too large: {len(serialized)} bytes")
                return False
            
            with open(file_path, 'wb') as f:
                f.write(serialized)
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing to file cache: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from file cache"""
        try:
            file_path = self._get_file_path(key)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting from file cache: {str(e)}")
            return False
    
    def clear(self) -> None:
        """Clear all file cache entries"""
        try:
            for file_path in self.cache_dir.glob("*.cache"):
                file_path.unlink(missing_ok=True)
        except Exception as e:
            logger.error(f"Error clearing file cache: {str(e)}")

# Global cache instances
_memory_cache = MemoryCache()
_async_memory_cache = AsyncMemoryCache()
_file_cache = FileCache()

def cache(ttl: int = 3600, use_file_cache: bool = False):
    """
    Decorator for caching function results
    
    Args:
        ttl: Time to live in seconds
        use_file_cache: Whether to use file-based cache
    """
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                cache_instance = _file_cache if use_file_cache else _async_memory_cache
                key = f"{func.__name__}:{_memory_cache._generate_key(*args, **kwargs)}"
                
                # Try to get from cache
                if use_file_cache:
                    result = cache_instance.get(key)
                else:
                    result = await cache_instance.aget(key)
                
                if result is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return result
                
                # Execute function and cache result
                logger.debug(f"Cache miss for {func.__name__}")
                result = await func(*args, **kwargs)
                
                if use_file_cache:
                    cache_instance.set(key, result, ttl)
                else:
                    await cache_instance.aset(key, result, ttl)
                
                return result
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                cache_instance = _file_cache if use_file_cache else _memory_cache
                key = f"{func.__name__}:{cache_instance._generate_key(*args, **kwargs)}"
                
                # Try to get from cache
                result = cache_instance.get(key)
                if result is not None:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return result
                
                # Execute function and cache result
                logger.debug(f"Cache miss for {func.__name__}")
                result = func(*args, **kwargs)
                cache_instance.set(key, result, ttl)
                
                return result
            return sync_wrapper
    return decorator

def clear_all_caches():
    """Clear all cache instances"""
    _memory_cache.clear()
    _async_memory_cache.clear()
    _file_cache.clear()
    logger.info("All caches cleared")

def get_cache_stats() -> Dict[str, Any]:
    """Get statistics for all caches"""
    return {
        'memory_cache': _memory_cache.get_stats(),
        'async_memory_cache': _async_memory_cache.get_stats(),
        'file_cache': {
            'cache_dir': str(_file_cache.cache_dir),
            'file_count': len(list(_file_cache.cache_dir.glob("*.cache")))
        }
    }
