import redis
import json
from typing import Any
from backend.core.config import settings

class CacheManager:
    def __init__(self):
        try:
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True
            )
        except Exception:
            self.redis = None

    def get(self, key: str):
        if not self.redis: return None
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def set(self, key: str, value: Any, ttl: int = 3600):
        if not self.redis: return
        self.redis.set(key, json.dumps(value), ex=ttl)
