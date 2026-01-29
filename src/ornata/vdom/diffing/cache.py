"""Caching for diffing operations."""

from collections import OrderedDict
from threading import RLock
from typing import Any


class DiffCache:
    """Cache for diffing operations to improve performance."""

    def __init__(self, max_size: int = 1000) -> None:
        """Initialize the diff cache."""
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._max_size = max_size
        self._lock = RLock()

    def __getitem__(self, key: str) -> Any:
        """Get an item from the cache."""
        with self._lock:
            if key in self._cache:
                # Move to end for LRU (most recently used)
                value = self._cache.pop(key)
                self._cache[key] = value
                return value
            return None

    def __setitem__(self, key: str, value: Any) -> None:
        """Set an item in the cache."""
        with self._lock:
            if key in self._cache:
                # Update existing key - move to end
                self._cache.pop(key)
            elif len(self._cache) >= self._max_size:
                # Remove least recently used (first item)
                self._cache.popitem(last=False)
            
            self._cache[key] = value

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache."""
        with self._lock:
            return key in self._cache

    def get(self, key: str, default: Any = None) -> Any:
        """Get item with default fallback."""
        with self._lock:
            if key in self._cache:
                value = self._cache.pop(key)
                self._cache[key] = value  # Move to end
                return value
            return default

    def clear(self) -> None:
        """Clear the cache."""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> dict[str, float | int]:
        """Get cache statistics."""
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "utilization": len(self._cache) / self._max_size if self._max_size > 0 else 0
            }
