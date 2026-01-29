from __future__ import annotations

from threading import Condition, RLock
from time import sleep
from typing import Any


class Lock:
    __slots__ = ("lock",)

    def __init__(self):
        self.lock = RLock()

    def __enter__(self):
        self.lock.acquire()

    def __exit__(self, exc_type: Any, exc: Any, tb: Any):
        self.lock.release()

    def acquire(self):
        self.lock.acquire()

    def release(self):
        self.lock.release()


# ============================================================
# READ-WRITE LOCK (multiple readers, one writer)
# ============================================================

class ReadWriteLock:
    __slots__ = ("readers", "lock", "cond")

    def __init__(self):
        self.readers = 0
        self.lock = RLock()
        self.cond = Condition(self.lock)

    def read_lock(self):
        return _ReadLock(self)

    def write_lock(self):
        return _WriteLock(self)


class _ReadLock:
    __slots__ = ("_parent",)

    def __init__(self, parent: ReadWriteLock):
        self._parent = parent

    def __enter__(self):
        with self._parent.lock:
            self._parent.readers += 1

    def __exit__(self, *_):
        with self._parent.lock:
            self._parent.readers -= 1
            if self._parent.readers == 0:
                self._parent.cond.notify_all()


class _WriteLock:
    __slots__ = ("_parent",)

    def __init__(self, parent: ReadWriteLock):
        self._parent = parent

    def __enter__(self):
        self._parent.lock.acquire()
        while self._parent.readers > 0:
            self._parent.cond.wait()

    def __exit__(self, *_):
        self._parent.lock.release()


# ============================================================
# SPINLOCK
# ============================================================

class SpinLock:
    __slots__ = ("_locked",)

    def __init__(self):
        self._locked = False

    def acquire(self):
        while True:
            if not self._locked:
                self._locked = True
                return
            sleep(0)

    def release(self):
        self._locked = False

    def __enter__(self):
        self.acquire()

    def __exit__(self, *_):
        self.release()


# ============================================================
# NO-OP LOCK
# ============================================================

class NoOpLock:
    """Useful for disabling locks without changing calling code."""

    def acquire(self): ...
    def release(self): ...
    def __enter__(self): ...
    def __exit__(self, *_): ...
