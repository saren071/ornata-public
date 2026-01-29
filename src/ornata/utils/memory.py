from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar

from .lock import Lock

if TYPE_CHECKING:
    from collections.abc import Callable

# ============================================================
# BASIC MEMORY POOLS
# ============================================================

_T = TypeVar("_T")


class MemoryPool(Generic[_T]):
    """Simple reusable-object pool with optional type metadata."""

    __slots__ = ("factory", "pool", "_free", "_max_size")

    def __class_getitem__(cls, _item: Any) -> type[MemoryPool[_T]]:
        """Allow typing syntax ``MemoryPool[T]`` without altering behaviour."""

        return cls

    def __init__(
        self,
        factory: Callable[[], _T] | type[_T],
        *,
        max_size: int | None = None,
        preallocate: int = 0,
    ) -> None:
        self.factory = factory  # Used to create new entries when none supplied.
        self.pool: list[_T | None] = []
        self._free: list[int] = []
        self._max_size = max_size
        if preallocate > 0:
            for _ in range(preallocate):
                self.pool.append(self._create())

    @property
    def max_size(self) -> int | None:
        """Return the configured maximum size for the pool."""
        return self._max_size

    # -- allocation ---------------------------------------------------------
    def allocate(self, value: _T | None = None) -> int:
        """Store ``value`` (or a factory product) and return its index."""

        item = value if value is not None else self._create()
        if self._free:
            idx = self._free.pop()
            self.pool[idx] = item
            return idx

        if self._max_size is not None and len(self.pool) >= self._max_size:
            raise MemoryError("MemoryPool full")

        self.pool.append(item)
        return len(self.pool) - 1

    def acquire(self) -> _T:
        """Acquire an instance from the pool, creating one when needed."""

        idx = self.allocate()
        value = self.pool[idx]
        if value is None:
            # Shouldn't happen, but guard for completeness.
            value = self._create()
            self.pool[idx] = value
        return value

    # -- lifetime -----------------------------------------------------------
    def free(self, index: int) -> None:
        """Mark the item at ``index`` as reusable."""

        if 0 <= index < len(self.pool) and self.pool[index] is not None:
            self.pool[index] = None
            self._free.append(index)

    def release(self, value: _T) -> None:
        """Return ``value`` to the pool if it exists inside the pool."""

        try:
            idx = self.pool.index(value)
        except ValueError:
            return
        self.free(idx)

    def clear(self) -> None:
        """Drop all cached entries."""

        self.pool.clear()
        self._free.clear()

    # -- helpers ------------------------------------------------------------
    def get(self, index: int) -> _T | None:
        return self.pool[index]

    def set(self, index: int, value: _T) -> None:
        self.pool[index] = value

    def _create(self) -> _T:
        return self.factory() if callable(self.factory) else self.factory()


class ThreadSafeMemoryPool(MemoryPool[_T]):
    """Thread-safe flavour of :class:`MemoryPool`."""

    __slots__ = ("_lock",)

    def __init__(
        self,
        factory: Callable[[], _T] | type[_T],
        *,
        max_size: int | None = None,
        preallocate: int = 0,
    ) -> None:
        super().__init__(factory, max_size=max_size, preallocate=preallocate)
        self._lock = Lock()

    def allocate(self, value: _T | None = None) -> int:
        with self._lock:
            return super().allocate(value)

    def acquire(self) -> _T:
        with self._lock:
            return super().acquire()

    def free(self, index: int) -> None:
        with self._lock:
            super().free(index)

    def release(self, value: _T) -> None:
        with self._lock:
            super().release(value)

    def clear(self) -> None:
        with self._lock:
            super().clear()

    def get(self, index: int) -> _T | None:
        with self._lock:
            return super().get(index)

    def set(self, index: int, value: _T) -> None:
        with self._lock:
            super().set(index, value)


# ============================================================
# SLAB ALLOCATOR
# ============================================================

class SlabAllocator:
    """
    Allocates objects of *fixed size*. Great for VDOM nodes, styles, etc.
    """

    __slots__ = ("_slab", "_free", "_capacity")

    def __init__(self, capacity: int):
        self._capacity = capacity
        self._slab: list[Any] = [None] * capacity
        self._free: list[int] = list(range(capacity))[::-1]

    def allocate(self, value: Any) -> int:
        if not self._free:
            raise MemoryError("Slab full")
        idx = self._free.pop()
        self._slab[idx] = value
        return idx

    def free(self, index: int):
        self._slab[index] = None
        self._free.append(index)

    def get(self, index: int) -> Any:
        return self._slab[index]

    def set(self, index: int, value: Any):
        self._slab[index] = value


class ThreadSafeSlabAllocator(SlabAllocator):
    __slots__ = ("_lock",)

    def __init__(self, capacity: int):
        super().__init__(capacity)
        self._lock = Lock()

    def allocate(self, value: Any) -> int:
        with self._lock:
            return super().allocate(value)

    def free(self, index: int):
        with self._lock:
            super().free(index)

    def get(self, index: int) -> Any:
        with self._lock:
            return super().get(index)

    def set(self, index: int, value: Any):
        with self._lock:
            super().set(index, value)


# ============================================================
# ARENA ALLOCATOR
# ============================================================

class ArenaAllocator:
    """
    Fast bump allocator. No per-object free, full reset only.
    """

    __slots__ = ("_arena", "_ptr", "_capacity")

    def __init__(self, capacity: int):
        self._capacity = capacity
        self._arena: list[Any] = [None] * capacity
        self._ptr = 0

    def allocate(self, value: Any) -> int:
        if self._ptr >= self._capacity:
            raise MemoryError("Arena full")
        idx = self._ptr
        self._arena[idx] = value
        self._ptr += 1
        return idx

    def reset(self):
        self._arena = [None] * self._capacity
        self._ptr = 0

    def get(self, index: int) -> Any:
        return self._arena[index]

    def set(self, index: int, value: Any):
        self._arena[index] = value


class ThreadSafeArenaAllocator(ArenaAllocator):
    __slots__ = ("_lock",)

    def __init__(self, capacity: int):
        super().__init__(capacity)
        self._lock = Lock()

    def allocate(self, value: Any) -> int:
        with self._lock:
            return super().allocate(value)

    def reset(self):
        with self._lock:
            super().reset()

    def get(self, index: int) -> Any:
        with self._lock:
            return super().get(index)

    def set(self, index: int, value: Any):
        with self._lock:
            super().set(index, value)
