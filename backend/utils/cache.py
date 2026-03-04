"""
Cache Manager Utility
- Manages Redis-based caching
- Implements robust error handling and loguru logging
"""
import redis
import json
from typing import Any, Optional
from loguru import logger
from backend.core.config import settings

class CacheManager:
    def __init__(self):
        self.redis = None
        try:
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True,
                socket_timeout=2.0
            )
            # Test connection
            self.redis.ping()
            logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.warning(f"Redis connection failed (caching disabled): {e}")
            self.redis = None

    def get(self, key: str) -> Optional[Any]:
        """Retrieves a value from the cache."""
        if not self.redis:
            return None
        try:
            data = self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Cache get failed for {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """Sets a value in the cache with a TTL."""
        if not self.redis:
            return
        try:
            self.redis.set(key, json.dumps(value), ex=ttl)
        except Exception as e:
            logger.error(f"Cache set failed for {key}: {e}")
