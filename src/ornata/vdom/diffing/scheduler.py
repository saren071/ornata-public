"""Effect scheduling and commit/effect phase separation for VDOM.

Goals:
- Separate "commit" (apply patches, bind/unbind) from "effects" (user lifecycle, side effects).
- Let render/diff stay pure and fast; run side effects after commit in a controlled queue.
- Offer both sync and async effect queues without forcing an event loop.

You can call into this scheduler from:
  - TreePatcher (after all patches are applied in a frame)
  - Lifecycle manager hooks (queue mount/update/unmount effects)
  - Renderer adapters (to coordinate frame boundaries)

"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any, Literal, overload

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import QueuedAsyncEffect, QueuedEffect

logger = get_logger(__name__)

Effect = Callable[[], Any]
AsyncEffect = Callable[[], Coroutine[Any, Any, Any]]
Priority = Literal[0, 1, 2]  # 0=high, 1=normal, 2=idle


class EffectScheduler:
    """Thread-safe effect scheduler with simple priority queues."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._high: list[QueuedEffect] = []
        self._norm: list[QueuedEffect] = []
        self._idle: list[QueuedEffect] = []

        self._ahigh: list[QueuedAsyncEffect] = []
        self._anorm: list[QueuedAsyncEffect] = []
        self._aidle: list[QueuedAsyncEffect] = []

        self._commit_depth = 0   # nesting counter to group effects per commit
        self._batch_mode = True  # if True, flush on end_commit()

    # ---------- Commit phase demarcation ----------

    def begin_commit(self) -> None:
        """Mark the start of a commit (patch application) batch."""
        with self._lock:
            self._commit_depth += 1
            logger.log(5, "Begin commit (depth=%d)", self._commit_depth)  # TRACE

    def end_commit(self) -> None:
        """Mark end of a commit; flush effects if we closed the outermost commit."""
        to_flush = False
        with self._lock:
            if self._commit_depth == 0:
                logger.warning("end_commit called without matching begin_commit")
                return
            self._commit_depth -= 1
            logger.log(5, "End commit (depth=%d)", self._commit_depth)  # TRACE
            if self._commit_depth == 0 and self._batch_mode:
                to_flush = True
        if to_flush:
            # Separate sync and async flush to keep deterministic order:
            self.flush_sync()
            # Auto-flush async effects if we have a running event loop
            try:
                loop = asyncio.get_running_loop()
                # In async context - schedule async effects to run
                asyncio.create_task(self.flush_async(loop=loop))
            except RuntimeError:
                # No event loop running - effects will be queued until explicitly flushed
                logger.debug("No event loop running, async effects queued")

    # ---------- Enqueue ----------

    def enqueue_effect(self, cb: Effect, *, priority: Priority = 1, label: str | None = None) -> None:
        from ornata.api.exports.definitions import QueuedEffect
        with self._lock:
            q: list[QueuedEffect] = self._pick_queue(priority, async_queue=False)
            q.append(QueuedEffect(cb=cb, priority=priority, label=label))
            logger.log(5, "Queue effect (prio=%s) %s", priority, label or cb.__name__)  # TRACE

    def enqueue_async_effect(
        self, factory: AsyncEffect, *, priority: Priority = 1, label: str | None = None
    ) -> None:
        from ornata.api.exports.definitions import QueuedAsyncEffect
        with self._lock:
            q: list[QueuedAsyncEffect] = self._pick_queue(priority, async_queue=True)
            q.append(QueuedAsyncEffect(factory=factory, priority=priority, label=label))
            logger.log(5, "Queue async effect (prio=%s) %s", priority, label or getattr(factory, "__name__", "async"))  # TRACE

    # ---------- Flush ----------

    def flush_sync(self, *, max_count: int | None = None) -> int:
        """Run queued sync effects in priority order. Returns number executed."""
        executed = 0
        while True:
            item = self._pop_next_sync()
            if item is None:
                break
            try:
                item.cb()
            except Exception as e:
                logger.error("Effect error (%s): %s", item.label or "unnamed", e)
            executed += 1
            if max_count is not None and executed >= max_count:
                break
        if executed:
            logger.log(5, "Flushed %d sync effects", executed)  # TRACE
        return executed

    async def flush_async(self, *, loop: asyncio.AbstractEventLoop | None = None, max_count: int | None = None) -> int:
        """Run queued async effects. If loop is provided, schedule there; otherwise run in current loop."""
        executed = 0
        while True:
            item = self._pop_next_async()
            if item is None:
                break
            try:
                coro: Coroutine[Any, Any, Any] = item.factory()
                if loop is None:
                    await coro
                else:
                    # schedule and wait; adjust if you prefer fire-and-forget
                    await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(coro, loop))
            except Exception as e:
                logger.error("Async effect error (%s): %s", item.label or "unnamed", e)
            executed += 1
            if max_count is not None and executed >= max_count:
                break
        if executed:
            logger.log(5, "Flushed %d async effects", executed)  # TRACE
        return executed

    # ---------- Lifecycle convenience (optional) ----------

    def on_component_mounted(self, *, label: str | None = None, cb: Effect | None = None) -> None:
        """Queue a mount effect (normal priority)."""
        # In many systems, this wraps calling user component.on_mount safely post-commit.
        if cb is not None:
            self.enqueue_effect(cb, priority=1, label=label or "on_mount")

    def on_component_updated(self, *, label: str | None = None, cb: Effect | None = None) -> None:
        """Queue an update effect (normal priority)."""
        if cb is not None:
            self.enqueue_effect(cb, priority=1, label=label or "on_update")

    def on_component_unmounted(self, *, label: str | None = None, cb: Effect | None = None) -> None:
        """Queue an unmount cleanup effect (high priority so it runs before idles)."""
        if cb is not None:
            self.enqueue_effect(cb, priority=0, label=label or "on_unmount")

    # ---------- Backend frame hooks (optional) ----------

    def on_frame_end(self) -> None:
        """Renderer can call this after presenting a frame to flush idle/low-priority tasks.
        
        This is called by renderer backends after presenting a frame to allow
        execution of idle and low-priority effects without blocking the main render pipeline.
        """
        # Drain idle tasks to keep UI responsive
        self.flush_sync(max_count=None)
        logger.debug("Frame end: flushed idle effects")

    # ---------- Internals ----------

    @overload
    def _pick_queue(self, priority: Priority, *, async_queue: Literal[False]) -> list[QueuedEffect]:
        ...

    @overload
    def _pick_queue(self, priority: Priority, *, async_queue: Literal[True]) -> list[QueuedAsyncEffect]:
        ...

    def _pick_queue(self, priority: Priority, *, async_queue: bool) -> list[QueuedEffect] | list[QueuedAsyncEffect]:
        if not async_queue:
            if priority == 0:
                return self._high
            if priority == 2:
                return self._idle
            return self._norm
        else:
            if priority == 0:
                return self._ahigh
            if priority == 2:
                return self._aidle
            return self._anorm

    def _pop_next_sync(self) -> QueuedEffect | None:
        with self._lock:
            if self._high:
                return self._high.pop(0)
            if self._norm:
                return self._norm.pop(0)
            if self._idle:
                return self._idle.pop(0)
            return None

    def _pop_next_async(self) -> QueuedAsyncEffect | None:
        with self._lock:
            if self._ahigh:
                return self._ahigh.pop(0)
            if self._anorm:
                return self._anorm.pop(0)
            if self._aidle:
                return self._aidle.pop(0)
            return None

    # ---------- Diagnostics ----------

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "sync_high": len(self._high),
                "sync_norm": len(self._norm),
                "sync_idle": len(self._idle),
                "async_high": len(self._ahigh),
                "async_norm": len(self._anorm),
                "async_idle": len(self._aidle),
                "commit_depth": self._commit_depth,
            }


# Per-thread scheduler so diff/commit can run in multiple threads safely.


def get_scheduler() -> EffectScheduler:
    """Thread-local accessor for the effect scheduler."""
    from ornata.api.exports.definitions import SCHED_LOCAL
    sch = getattr(SCHED_LOCAL, "scheduler", None)
    if sch is None:
        sch = EffectScheduler()
        SCHED_LOCAL.scheduler = sch
    return sch


# -------- Integration recipe (non-executable reference) --------
#
# In your GUI/CLI frame pump:
#   - after presenting a frame, consider sch.on_frame_end()
#   - if you have an asyncio loop, periodically await sch.flush_async(loop=loop)
#
