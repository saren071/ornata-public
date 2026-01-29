from __future__ import annotations

from collections import OrderedDict
from threading import RLock
from time import monotonic
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


# ============================================================
# SIMPLE CACHE (UNSAFE)
# ============================================================

class SimpleCache(Generic[K, V]):
    __slots__ = ("_store",)

    def __init__(self) -> None:
        self._store: dict[K, V] = {}

    # Base ops ------------------------------------------------

    def get(self, key: K, default: V | None = None) -> V | None:
        return self._store.get(key, default)

    def set(self, key: K, value: V) -> None:
        self._store[key] = value

    def remove(self, key: K) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    # Dict-like ----------------------------------------------

    def __getitem__(self, key: K) -> V:
        if key not in self._store:
            raise KeyError(key)
        return self._store[key]

    def __setitem__(self, key: K, value: V) -> None:
        self._store[key] = value

    def __contains__(self, key: K) -> bool:
        return key in self._store

    def __len__(self) -> int:
        return len(self._store)


# ============================================================
# SIMPLE CACHE (THREAD-SAFE)
# ============================================================

class ThreadSafeSimpleCache(Generic[K, V]):
    __slots__ = ("_store", "_lock")

    def __init__(self) -> None:
        self._store: dict[K, V] = {}
        self._lock = RLock()

    # Base ops ------------------------------------------------

    def get(self, key: K, default: V | None = None) -> V | None:
        with self._lock:
            return self._store.get(key, default)

    def set(self, key: K, value: V) -> None:
        with self._lock:
            self._store[key] = value

    def remove(self, key: K) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    # Dict-like ----------------------------------------------

    def __getitem__(self, key: K) -> V:
        with self._lock:
            if key not in self._store:
                raise KeyError(key)
            return self._store[key]

    def __setitem__(self, key: K, value: V) -> None:
        with self._lock:
            self._store[key] = value

    def __contains__(self, key: K) -> bool:
        with self._lock:
            return key in self._store

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)


# ============================================================
# LRU CACHE (UNSAFE)
# ============================================================

class LRUCache(Generic[K, V]):
    __slots__ = ("_store", "_max_size")

    def __init__(self, max_size: int = 128) -> None:
        self._store: OrderedDict[K, V] = OrderedDict()
        self._max_size = max_size

    # Base ops ------------------------------------------------

    def get(self, key: K, default: V | None = None) -> V | None:
        if key not in self._store:
            return default
        val = self._store.pop(key)
        self._store[key] = val
        return val

    def set(self, key: K, value: V) -> None:
        if key in self._store:
            self._store.pop(key)
        self._store[key] = value
        if len(self._store) > self._max_size:
            self._store.popitem(last=False)

    def remove(self, key: K) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    # Dict-like ----------------------------------------------

    def __getitem__(self, key: K) -> V:
        val = self.get(key)
        if val is None:
            raise KeyError(key)
        return val

    def __setitem__(self, key: K, value: V) -> None:
        self.set(key, value)

    def __contains__(self, key: K) -> bool:
        return key in self._store

    def __len__(self) -> int:
        return len(self._store)


# ============================================================
# LRU CACHE (THREAD-SAFE)
# ============================================================

class ThreadSafeLRUCache(Generic[K, V]):
    __slots__ = ("_store", "_max_size", "_lock", "_hits", "_misses")

    def __init__(self, max_size: int = 128) -> None:
        self._store: OrderedDict[K, V] = OrderedDict()
        self._max_size = max_size
        self._lock = RLock()
        self._hits = 0
        self._misses = 0

    def get(self, key: K, default: V | None = None) -> V | None:
        with self._lock:
            if key not in self._store:
                self._misses += 1
                return default
            value = self._store.pop(key)
            self._store[key] = value
            self._hits += 1
            return value

    def set(self, key: K, value: V) -> None:
        with self._lock:
            if key in self._store:
                self._store.pop(key)
            self._store[key] = value

            if len(self._store) > self._max_size:
                self._store.popitem(last=False)
    
    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict[str, int | float]:
        """Return cache statistics for monitoring."""
        with self._lock:
            size = len(self._store)
            total = self._hits + self._misses
            hit_rate = self._hits / total if total else 0.0
            return {
                "size": size,
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
            }

    # Dict-like ----------------------------------------------

    def __getitem__(self, key: K) -> V:
        val = self.get(key)
        if val is None:
            raise KeyError(key)
        return val

    def __setitem__(self, key: K, value: V) -> None:
        self.set(key, value)

    def __contains__(self, key: K) -> bool:
        with self._lock:
            return key in self._store

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)


# ============================================================
# TTL CACHE (UNSAFE)
# ============================================================

class TTLCache(Generic[K, V]):
    __slots__ = ("_store", "_ttl")

    def __init__(self, ttl_seconds: float = 5.0) -> None:
        self._store: dict[K, tuple[float, V]] = {}
        self._ttl = ttl_seconds

    # Base ops ------------------------------------------------

    def get(self, key: K, default: V | None = None) -> V | None:
        now = monotonic()
        entry = self._store.get(key)
        if entry is None:
            return default
        expires, val = entry
        if now > expires:
            self._store.pop(key, None)
            return default
        return val

    def set(self, key: K, value: V) -> None:
        self._store[key] = (monotonic() + self._ttl, value)

    def remove(self, key: K) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    # Dict-like ----------------------------------------------

    def __getitem__(self, key: K) -> V:
        val = self.get(key)
        if val is None:
            raise KeyError(key)
        return val

    def __setitem__(self, key: K, value: V) -> None:
        self.set(key, value)

    def __contains__(self, key: K) -> bool:
        return key in self._store

    def __len__(self) -> int:
        return len(self._store)


# ============================================================
# TTL CACHE (THREAD-SAFE)
# ============================================================

class ThreadSafeTTLCache(Generic[K, V]):
    __slots__ = ("_store", "_ttl", "_lock")

    def __init__(self, ttl_seconds: float = 5.0) -> None:
        self._store: dict[K, tuple[float, V]] = {}
        self._ttl = ttl_seconds
        self._lock = RLock()

    # Base ops ------------------------------------------------

    def get(self, key: K, default: V | None = None) -> V | None:
        with self._lock:
            now = monotonic()
            entry = self._store.get(key)
            if entry is None:
                return default
            expires, val = entry
            if now > expires:
                self._store.pop(key, None)
                return default
            return val

    def set(self, key: K, value: V) -> None:
        with self._lock:
            self._store[key] = (monotonic() + self._ttl, value)

    def remove(self, key: K) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    # Dict-like ----------------------------------------------

    def __getitem__(self, key: K) -> V:
        val = self.get(key)
        if val is None:
            raise KeyError(key)
        return val

    def __setitem__(self, key: K, value: V) -> None:
        self.set(key, value)

    def __contains__(self, key: K) -> bool:
        with self._lock:
            return key in self._store

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)


# ============================================================
# LFU CACHE (UNSAFE)
# ============================================================

class LFUCache(Generic[K, V]):
    __slots__ = ("_store", "_freq", "_max_size")

    def __init__(self, max_size: int = 128) -> None:
        self._store: dict[K, V] = {}
        self._freq: dict[K, int] = {}
        self._max_size = max_size

    # Base ops ------------------------------------------------

    def get(self, key: K, default: V | None = None) -> V | None:
        if key not in self._store:
            return default
        self._freq[key] += 1
        return self._store[key]

    def set(self, key: K, value: V) -> None:
        if key in self._store:
            self._store[key] = value
            self._freq[key] += 1
            return

        if len(self._store) >= self._max_size:
            least = min(self._freq.items(), key=lambda x: x[1])[0]
            self._store.pop(least, None)
            self._freq.pop(least, None)

        self._store[key] = value
        self._freq[key] = 1

    def remove(self, key: K) -> None:
        self._store.pop(key, None)
        self._freq.pop(key, None)

    def clear(self) -> None:
        self._store.clear()
        self._freq.clear()

    # Dict-like ----------------------------------------------

    def __getitem__(self, key: K) -> V:
        val = self.get(key)
        if val is None:
            raise KeyError(key)
        return val

    def __setitem__(self, key: K, value: V) -> None:
        self.set(key, value)

    def __contains__(self, key: K) -> bool:
        return key in self._store

    def __len__(self) -> int:
        return len(self._store)


# ============================================================
# LFU CACHE (THREAD-SAFE)
# ============================================================

class ThreadSafeLFUCache(Generic[K, V]):
    __slots__ = ("_store", "_freq", "_max_size", "_lock")

    def __init__(self, max_size: int = 128) -> None:
        self._store: dict[K, V] = {}
        self._freq: dict[K, int] = {}
        self._max_size = max_size
        self._lock = RLock()

    # Base ops ------------------------------------------------

    def get(self, key: K, default: V | None = None) -> V | None:
        with self._lock:
            if key not in self._store:
                return default
            self._freq[key] += 1
            return self._store[key]

    def set(self, key: K, value: V) -> None:
        with self._lock:
            if key in self._store:
                self._store[key] = value
                self._freq[key] += 1
                return

            if len(self._store) >= self._max_size:
                least = min(self._freq.items(), key=lambda x: x[1])[0]
                self._store.pop(least, None)
                self._freq.pop(least, None)

            self._store[key] = value
            self._freq[key] = 1

    def remove(self, key: K) -> None:
        with self._lock:
            self._store.pop(key, None)
            self._freq.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()
            self._freq.clear()

    # Dict-like ----------------------------------------------

    def __getitem__(self, key: K) -> V:
        val = self.get(key)
        if val is None:
            raise KeyError(key)
        return val

    def __setitem__(self, key: K, value: V) -> None:
        self.set(key, value)

    def __contains__(self, key: K) -> bool:
        with self._lock:
            return key in self._store

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)
