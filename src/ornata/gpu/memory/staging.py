"""GPU staging buffer management for efficient CPU-GPU data transfer."""

from __future__ import annotations

import struct
import threading
from collections import deque
from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import TransferDirection, TransferRequest
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:

    from ornata.gpu.misc import GPUBackend

logger = get_logger(__name__)


class Staging:
    """Manages staging buffers for efficient CPU-GPU data transfers."""

    def __init__(self, backend: GPUBackend | None = None, staging_buffer_size: int = 64 * 1024 * 1024) -> None:
        """Initialize the staging buffer manager.

        Args:
            backend: GPU backend for staging operations.
            staging_buffer_size: Size of staging buffers in bytes.
        """
        self.backend = backend
        self.staging_buffer_size = staging_buffer_size
        self._lock = threading.RLock()

        # Transfer queues by priority
        self._transfer_queues: dict[int, deque[TransferRequest]] = {}
        self._active_transfers: set[str] = set()

        # Staging buffer pool
        self._staging_buffers: list[Any] = []
        self._available_buffers: deque[Any] = deque()

        # Statistics
        self._stats = {
            "transfers_completed": 0,
            "bytes_transferred": 0,
            "average_transfer_time": 0.0,
            "peak_queue_size": 0
        }

    def queue_transfer(self, request: TransferRequest) -> None:
        """Queue a data transfer request.

        Args:
            request: Transfer request to queue.
        """
        with self._lock:
            if request.id in self._active_transfers:
                from ornata.api.exports.definitions import GPUMemoryError
                raise GPUMemoryError(f"Transfer {request.id} already in progress")

            queue = self._transfer_queues.setdefault(request.priority, deque())
            queue.append(request)
            self._active_transfers.add(request.id)

            queue_size = sum(len(q) for q in self._transfer_queues.values())
            if queue_size > self._stats["peak_queue_size"]:
                self._stats["peak_queue_size"] = queue_size

            logger.debug(f"Queued transfer {request.id} ({request.size} bytes, {request.direction.value})")

    def process_transfers(self, max_transfers: int | None = None) -> int:
        """Process pending transfer requests.

        Args:
            max_transfers: Maximum number of transfers to process, or None for all.

        Returns:
            Number of transfers completed.
        """
        with self._lock:
            completed = 0
            processed_priorities = sorted(self._transfer_queues.keys(), reverse=True)  # Higher priority first

            for priority in processed_priorities:
                queue = self._transfer_queues[priority]
                while queue and (max_transfers is None or completed < max_transfers):
                    request = queue.popleft()
                    if self._execute_transfer(request):
                        completed += 1
                        self._stats["transfers_completed"] += 1
                        self._stats["bytes_transferred"] += request.size
                        self._active_transfers.discard(request.id)

                        # Execute callback if provided
                        if request.callback:
                            try:
                                request.callback(request)
                            except Exception as e:
                                logger.warning(f"Transfer callback failed for {request.id}: {e}")

            return completed

    def create_staging_buffer(self) -> Any:
        """Create a new staging buffer.

        Returns:
            GPU staging buffer object.

        Raises:
            GPUMemoryError: If buffer creation fails.
        """
        with self._lock:
            if self.backend is None:
                from ornata.api.exports.definitions import GPUMemoryError
                raise GPUMemoryError("No GPU backend available for staging buffer creation")

            try:
                buffer = bytearray(self.staging_buffer_size)
                self._staging_buffers.append(buffer)
                self._available_buffers.append(buffer)
                return buffer
            except Exception as e:
                from ornata.api.exports.definitions import GPUMemoryError
                raise GPUMemoryError(f"Failed to create staging buffer: {e}") from e

    def get_staging_buffer(self) -> Any | None:
        """Get an available staging buffer from the pool.

        Returns:
            Available staging buffer, or None if none available.
        """
        with self._lock:
            if self._available_buffers:
                return self._available_buffers.popleft()
            return None

    def return_staging_buffer(self, buffer: Any) -> None:
        """Return a staging buffer to the pool.

        Args:
            buffer: Buffer to return.
        """
        with self._lock:
            if buffer in self._staging_buffers and buffer not in self._available_buffers:
                self._available_buffers.append(buffer)

    def get_transfer_stats(self) -> dict[str, int | float]:
        """Get transfer statistics.

        Returns:
            Dictionary with transfer statistics.
        """
        with self._lock:
            active_transfers = len(self._active_transfers)
            queued_transfers = sum(len(q) for q in self._transfer_queues.values())

            return {
                "transfers_completed": self._stats["transfers_completed"],
                "bytes_transferred": self._stats["bytes_transferred"],
                "active_transfers": active_transfers,
                "queued_transfers": queued_transfers,
                "total_pending_transfers": active_transfers + queued_transfers,
                "peak_queue_size": self._stats["peak_queue_size"],
                "available_staging_buffers": len(self._available_buffers),
                "total_staging_buffers": len(self._staging_buffers)
            }

    def cancel_transfer(self, transfer_id: str) -> bool:
        """Cancel a pending transfer request.

        Args:
            transfer_id: ID of the transfer to cancel.

        Returns:
            True if transfer was cancelled, False if not found.
        """
        with self._lock:
            # Check active transfers
            if transfer_id in self._active_transfers:
                self._active_transfers.discard(transfer_id)
                return True

            # Check queued transfers
            for queue in self._transfer_queues.values():
                for request in queue:
                    if request.id == transfer_id:
                        queue.remove(request)
                        return True

            return False

    def flush_all_transfers(self) -> int:
        """Flush all pending transfers.

        Returns:
            Number of transfers completed.
        """
        return self.process_transfers(max_transfers=None)

    def cleanup(self) -> None:
        """Clean up staging buffer manager state."""
        with self._lock:
            # Cancel all pending transfers
            for queue in self._transfer_queues.values():
                queue.clear()
            self._transfer_queues.clear()
            self._active_transfers.clear()

            # Clear staging buffers
            self._staging_buffers.clear()
            self._available_buffers.clear()

            logger.debug("Staging buffer manager cleaned up")

    def _execute_transfer(self, request: TransferRequest) -> bool:
        """Execute a transfer request.

        Args:
            request: Transfer request to execute.

        Returns:
            True if transfer succeeded.
        """
        try:
            if self.backend is None:
                return False

            # Get or create staging buffer
            staging_buffer = self.get_staging_buffer()
            if staging_buffer is None:
                staging_buffer = self.create_staging_buffer()

            # Backend-specific transfer logic would be implemented here
            success = self._perform_transfer(request, staging_buffer)

            # Return staging buffer to pool
            self.return_staging_buffer(staging_buffer)

            if success:
                logger.debug(f"Completed transfer {request.id}")
            else:
                logger.warning(f"Transfer {request.id} failed")

            return success

        except Exception as e:
            logger.error(f"Transfer execution failed for {request.id}: {e}")
            return False

    def _perform_transfer(self, request: TransferRequest, staging_buffer: Any) -> bool:
        """Perform the actual data transfer.

        Args:
            request: Transfer request.
            staging_buffer: Staging buffer to use.

        Returns:
            True if transfer succeeded.

        Raises:
            GPUMemoryError: If transfer fails due to backend issues.
        """
        try:
            if request.direction is TransferDirection.CPU_TO_GPU:
                # CPU to GPU transfer: copy data to staging buffer
                if isinstance(staging_buffer, bytearray):
                    data_bytes = _coerce_transfer_data(request.data)
                    if len(data_bytes) > len(staging_buffer):
                        from ornata.api.exports.definitions import GPUMemoryError
                        raise GPUMemoryError(f"Data size {len(data_bytes)} exceeds staging buffer size {len(staging_buffer)}")
                    staging_buffer[: len(data_bytes)] = data_bytes

                    # If we have a real GPU backend, perform actual GPU upload
                    if self.backend is not None and hasattr(self.backend, 'upload_to_gpu'):
                        try:
                            self.backend.upload_to_gpu(staging_buffer, request.size)
                            logger.debug(f"Uploaded {request.size} bytes to GPU")
                        except Exception as gpu_e:
                            logger.warning(f"GPU upload failed, falling back to CPU operation: {gpu_e}")
                            # Continue as CPU operation
                    else:
                        logger.debug(f"Staged {request.size} bytes for CPU-to-GPU transfer (no GPU backend available)")

            elif request.direction is TransferDirection.GPU_TO_CPU:
                # GPU to CPU transfer: download data from GPU to staging buffer
                if isinstance(staging_buffer, bytearray):
                    if self.backend is not None and hasattr(self.backend, 'download_from_gpu'):
                        try:
                            # Download from GPU to staging buffer
                            bytes_downloaded = self.backend.download_from_gpu(staging_buffer, request.size)
                            logger.debug(f"Downloaded {bytes_downloaded} bytes from GPU")

                            # Convert back to requested data format and store in request
                            if isinstance(request.data, bytes):
                                request.data = bytes(staging_buffer[:bytes_downloaded])
                            elif isinstance(request.data, list):
                                if request.data and isinstance(request.data[0], float):
                                    # Convert bytes back to float list
                                    float_count = bytes_downloaded // 4
                                    request.data = list(struct.unpack(f'{float_count}f', staging_buffer[:bytes_downloaded]))
                                else:
                                    # Convert bytes back to int list
                                    int_count = bytes_downloaded // 4
                                    request.data = list(struct.unpack(f'{int_count}i', staging_buffer[:bytes_downloaded]))

                        except Exception as gpu_e:
                            logger.warning(f"GPU download failed: {gpu_e}")
                            from ornata.api.exports.definitions import GPUMemoryError
                            raise GPUMemoryError(f"GPU download failed: {gpu_e}") from gpu_e
                    else:
                        logger.warning("GPU_TO_CPU transfer requested but no GPU backend available")
                        from ornata.api.exports.definitions import GPUMemoryError
                        raise GPUMemoryError("GPU_TO_CPU transfer requires GPU backend")

            return True

        except Exception as e:
            logger.error(f"Data transfer failed: {e}")
            from ornata.api.exports.definitions import GPUMemoryError
            raise GPUMemoryError(f"Transfer operation failed: {e}") from e


def _coerce_transfer_data(data: list[float] | list[int] | bytes) -> bytes:
    if isinstance(data, bytes):
        return data
    if isinstance(data, list):
        if data and isinstance(data[0], float):
            return bytes(int(max(0.0, min(255.0, value * 255))) for value in data)
        return bytes(int(max(0, min(255, value))) for value in data)
    return bytes(data)