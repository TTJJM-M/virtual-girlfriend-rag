from functools import lru_cache
from typing import Any, Dict
import time


class LRUCache:
    """Simple LRU cache for query results"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: Dict[str, Any] = {}
        self.timestamps: Dict[str, float] = {}

    def get(self, key: str) -> Any:
        """Get value if exists and not expired (5 min TTL)"""
        if key in self.cache:
            if time.time() - self.timestamps[key] < 300:  # 5 min TTL
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None

    def set(self, key: str, value: Any):
        """Set value, evicting oldest if needed"""
        if len(self.cache) >= self.max_size:
            # Evict oldest
            oldest_key = min(self.timestamps, key=self.timestamps.get)
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]

        self.cache[key] = value
        self.timestamps[key] = time.time()

    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.timestamps.clear()


# Global cache instance
query_cache = LRUCache(max_size=1000)
