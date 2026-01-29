"""Asynchronous event processing for Ornata."""

from __future__ import annotations

import threading
import time
from collections import deque
from concurrent.futures import Future, ThreadPoolExecutor
from tracemalloc import Traceback
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.api.exports.definitions import Event

logger = get_logger(__name__)


class AsyncEventProcessor:
    """Thread-pool backed processor for asynchronous event dispatch with high-throughput optimizations."""

    def __init__(self, max_workers: int | None = None, queue_size: int | None = None) -> None:
        """Create the processor with free-threading compatibility.

        Args:
            max_workers: Optional worker limit for the internal pool. When not
                provided a heuristic based on the active thread count is used.
            queue_size: Optional queue size for the internal pool. When not
                provided a heuristic based on the active thread count is used.
        """

        # Free-threading compatible: use thread pool instead of asyncio for GIL-free operation
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers or min(32, threading.active_count() * 2),
            thread_name_prefix="event-processor",
        )
        self._running = True
        self._lock = threading.RLock()
        # Aggressive batching for 1M+ ops/s
        self._batch_size = 500  # Increased batch size
        self._batch_timeout = 0.0005  # Reduced to 0.5ms for faster processing
        self._current_batch: list[tuple[Event, Callable[[Event], Any]]] = []
        self._last_batch_time = time.perf_counter()
        self._batch_lock = threading.RLock()
        # Pre-allocate batch lists to reduce allocations
        self._batch_pool: deque[list[tuple[Event, Callable[[Event], Any]]]] = deque(maxlen=10)
        for _ in range(5):
            self._batch_pool.append([])

    def process_event_async(self, event: Event, handler: Callable[[Event], Any]) -> None:
        """Dispatch ``event`` to ``handler`` in the background with batching.

        Args:
            event: Event to process asynchronously.
            handler: Callable invoked by a worker thread.
        """

        if not self._running:
            logger.warning("Async processor is shutting down, ignoring event")
            return

        # Add to batch for high-throughput processing
        with self._batch_lock:
            self._current_batch.append((event, handler))

            # Check if batch should be flushed
            current_time = time.perf_counter()
            should_flush = (
                len(self._current_batch) >= self._batch_size or
                (current_time - self._last_batch_time) >= self._batch_timeout
            )

            if should_flush:
                batch = self._current_batch[:]
                self._current_batch.clear()
                self._last_batch_time = current_time
                self._submit_batch(batch)
            else:
                # Schedule flush timer if this is the first item in batch
                if len(self._current_batch) == 1:
                    self._schedule_batch_flush()

    def process_event_sync(self, event: Event, handler: Callable[[Event], Any]) -> Any:
        """Run ``handler`` synchronously for testing scenarios.

        Args:
            event: Event to process.
            handler: Callable executed inline.

        Returns:
            Any: Result returned by ``handler``.
        """

        return self._execute_handler(event, handler)

    def shutdown(self, wait: bool = True) -> None:
        """Stop accepting new events and optionally wait for completion.

        Args:
            wait: When ``True`` blocks until all queued work completes.
        """

        with self._lock:
            if not self._running:
                return
            self._running = False

        # Flush any remaining batch
        with self._batch_lock:
            if self._current_batch:
                batch = self._current_batch[:]
                self._current_batch.clear()
                self._submit_batch(batch)

        logger.debug("Shutting down AsyncEventProcessor")
        self._executor.shutdown(wait=wait)

    def get_active_count(self) -> int:
        """Return the number of currently active worker threads.

        Returns:
            int: Number of active threads in the interpreter.
        """

        return threading.active_count()

    def get_queue_size(self) -> int:
        """Return the current approximate queue length.

        Returns:
            int: Number of pending work items.
        """

        queue = getattr(self._executor, "_work_queue", None)
        if queue is None:
            return 0
        try:
            return queue.qsize()
        except Exception as e:
            logger.debug(f"Error: {e}, Traceback: {Traceback}")
            return 0

    def _submit_batch(self, batch: list[tuple[Event, Callable[[Event], Any]]]) -> None:
        """Submit a batch of events for processing."""
        if not batch:
            return

        future = self._executor.submit(self._execute_batch, batch)
        future.add_done_callback(lambda fut: self._handle_batch_completion(fut, batch))

    def _schedule_batch_flush(self) -> None:
        """Schedule a batch flush after timeout."""
        def flush_batch() -> None:
            with self._batch_lock:
                if self._current_batch:
                    batch = self._current_batch[:]
                    self._current_batch.clear()
                    self._submit_batch(batch)

        # Use thread pool to schedule flush (free-threading compatible)
        self._executor.submit(self._delayed_flush, flush_batch, self._batch_timeout)

    def _delayed_flush(self, func: Callable[[], None], delay: float) -> None:
        """Execute function after delay."""
        time.sleep(delay)
        func()

    def _execute_batch(self, batch: list[tuple[Event, Callable[[Event], Any]]]) -> None:
        """Execute a batch of event handlers."""
        for event, handler in batch:
            try:
                self._execute_handler(event, handler)
            except Exception as exc:
                logger.warning("Batch handler failure for %s: %s", event.type.value, exc)

    def _execute_handler(self, event: Event, handler: Callable[[Event], Any]) -> Any:
        """Execute ``handler`` and capture execution time for diagnostics.

        Args:
            event: Event passed to the handler.
            handler: Callable being executed.

        Returns:
            Any: Result produced by the handler.

        Raises:
            EventError: When the handler raises an exception.
        """

        try:
            logger.log(5, "Executing handler for %s", event.type.value)
            start_time = time.perf_counter()
            result = handler(event)
            duration = time.perf_counter() - start_time
            logger.log(5, "Handler completed in %.3fs", duration)
            return result
        except Exception as exc:
            from ornata.api.exports.definitions import EventError
            logger.error("Event handler failure for %s: %s", event.type.value, exc)
            raise EventError(f"Event handler execution failed: {exc}") from exc

    def _handle_batch_completion(self, future: Future[Any], batch: list[tuple[Event, Callable[[Event], Any]]]) -> None:
        """Log completion state for asynchronous batch work.

        Args:
            future: Future returned by batch processing.
            batch: The batch that was processed.

        Returns:
            None
        """

        try:
            exception = future.exception()
            if exception:
                logger.warning("Async batch processing failed: %s", exception)
            else:
                logger.log(5, "Async batch processing completed for %d events", len(batch))
        except Exception as exc:
            logger.warning("Batch completion callback failed: %s", exc)


class EventQueue:
    """Bounded, thread-safe queue proxying ``LockFreeEventQueue`` for processors."""

    def __init__(self, max_size: int = 1000) -> None:
        from ornata.events.core.bus import LockFreeEventQueue
        self._shutdown = False
        self._lock = threading.RLock()
        self._queue = LockFreeEventQueue(max_size=max_size)

    def put(self, event: Event) -> bool:
        """Insert ``event`` into the queue.

        Args:
            event: Event to enqueue.

        Returns:
            bool: ``True`` when the event was enqueued.

        Raises:
            EventError: When the queue has been shut down.
        """

        if self._shutdown:
            from ornata.api.exports.definitions import EventError
            raise EventError("Queue is shutdown")

        return self._queue.put(event)

    def get(self) -> Event | None:
        """Retrieve the next event from the queue."""

        batch = self._queue.get_batch(1)
        return batch[0] if batch else None

    def shutdown(self) -> None:
        """Wake waiting processors and prevent further enqueue operations."""

        with self._lock:
            self._shutdown = True

    def size(self) -> int:
        return self._queue.size()

    def empty(self) -> bool:
        return self._queue.size() == 0


class BatchedEventProcessor:
    """Batching helper that coalesces events for efficient handling with high-throughput optimizations."""

    def __init__(self, batch_size: int = 10, flush_interval: float = 0.1) -> None:
        """Create a batching processor.

        Args:
            batch_size: Maximum number of events per batch.
            flush_interval: Maximum interval in seconds before a forced flush.
        """

        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._batch: list[tuple[Event, Callable[[Event], Any]]] = []
        self._last_flush = time.time()
        self._lock = threading.RLock()

    def add_event(self, event: Event, handler: Callable[[Event], Any]) -> None:
        """Add an event to the current batch.

        Args:
            event: Event to add to the batch.
            handler: Handler responsible for processing the event.

        Returns:
            None
        """

        with self._lock:
            self._batch.append((event, handler))
            if self._should_flush():
                self._flush_batch()

    def flush(self) -> None:
        """Flush the batch immediately.

        Returns:
            None
        """

        with self._lock:
            self._flush_batch()

    def _should_flush(self) -> bool:
        """Return whether the current batch should be flushed.

        Returns:
            bool: ``True`` when size or time thresholds have been met.
        """

        size_exceeded = len(self._batch) >= self._batch_size
        time_exceeded = (time.time() - self._last_flush) >= self._flush_interval
        return size_exceeded or time_exceeded

    def _flush_batch(self) -> None:
        """Process the current batch and reset state."""

        if not self._batch:
            return

        batch = list(self._batch)
        self._batch.clear()
        self._last_flush = time.time()

        for event, handler in batch:
            try:
                handler(event)
            except Exception as exc:
                logger.warning("Batched handler failure for %s: %s", event.type.value, exc)


__all__ = [
    "AsyncEventProcessor",
    "BatchedEventProcessor",
    "EventQueue",
]