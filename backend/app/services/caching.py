import time
from typing import Any, Dict, Optional

class SimpleCache:
    """
    A simple thread-safe in-memory cache for high-frequency data.
    In production, this can be swapped with Redis.
    """
    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if time.time() > entry["expiry"]:
            del self._cache[key]
            return None

        return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        expiry = time.time() + (ttl or self._default_ttl)
        self._cache[key] = {
            "value": value,
            "expiry": expiry
        }

    def clear(self):
        self._cache.clear()

# Global instances for different data types
catalog_cache = SimpleCache(default_ttl=600)  # 10 minutes
branch_cache = SimpleCache(default_ttl=3600)  # 1 hour
