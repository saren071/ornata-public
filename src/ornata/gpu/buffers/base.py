"""Base class for GPU buffer objects."""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ornata.api.exports.definitions import BackendTarget, BufferUsage

# Define a type variable constrained to int and float
T = TypeVar("T", int, float)


class GPUBuffer[T: (int, float)](ABC):
    """Abstract base class for GPU buffer objects with comprehensive error handling."""

    def __init__(self, data: Sequence[T], usage: str) -> None:
        """Initialize GPU buffer with data.

        Args:
            data: The buffer data as a list of ints or floats.
            usage: Buffer usage pattern ('static', 'dynamic', 'stream').
            
        Raises:
            GPUBufferAlignmentError: If data validation fails
        """
        # Validate input data
        from ornata.api.exports.definitions import BufferUsage
        from ornata.gpu.buffers.utils import validate_buffer_data
        validate_buffer_data(list(data))
        
        self._data: list[T] = list(data)
        self._usage: BufferUsage = BufferUsage(usage) if usage in [e.value for e in BufferUsage] else BufferUsage.DYNAMIC
        self._buffer_id: int | None = None
        self._com_object: object | None = None  # For DirectX COM objects
        self._backend_kind: BackendTarget | None = None
        self._lock = threading.RLock()
        self._is_bound: bool = False
        self._last_accessed: float | None = None

    @property
    def data(self) -> list[T]:
        """Get the buffer data."""
        with self._lock:
            self._last_accessed = __import__('time').time()
            return self._data.copy()

    @property
    def usage(self) -> str:
        """Get the buffer usage pattern."""
        return self._usage.value

    @property
    def backend_kind(self) -> BackendTarget | None:
        """Get the active backend kind."""
        return self._backend_kind

    @property
    def is_bound(self) -> bool:
        """Check if buffer is currently bound."""
        with self._lock:
            return self._is_bound

    @property
    def buffer_size_bytes(self) -> int:
        """Get buffer size in bytes."""
        return len(self._data) * 4  # 4 bytes per float/int

    def update_data(self, data: Sequence[T]) -> None:
        """Update buffer data with validation and error handling.

        Args:
            data: New data to store in the buffer.

        Raises:
            GPUBufferAlignmentError: If data validation fails
            ValueError: If data format is incompatible
        """
        with self._lock:
            # Validate new data
            from ornata.gpu.buffers.utils import log_buffer_operation, validate_buffer_data
            validate_buffer_data(list(data))
            
            if len(data) != len(self._data):
                # Size changed - may need to recreate GPU buffer
                old_size = self.buffer_size_bytes
                self._data = list(data)
                self._on_size_changed(old_size)
                log_buffer_operation("resized", self._get_buffer_info(), True,
                                   f"size change: {old_size} -> {self.buffer_size_bytes} bytes")
            else:
                # Same size - just update data
                old_data = self._data
                self._data = list(data)
                log_buffer_operation("updated", self._get_buffer_info(), True,
                                   f"data update: {len(old_data)} -> {len(data)} elements")

    def _on_size_changed(self, old_size_bytes: int) -> None:
        """Handle buffer size changes - subclasses should override."""
        self._update_gpu_buffer_if_needed()

    @abstractmethod
    def _update_gpu_buffer_if_needed(self) -> None:
        """Update GPU buffer if buffer size has changed."""
        # Subclasses should implement this to handle size changes
        pass

    def bind(self) -> bool:
        """Bind the buffer for GPU operations.

        Returns:
            True if binding succeeded, False otherwise
        """
        from ornata.gpu.buffers.utils import log_buffer_operation
        with self._lock:
            try:
                success = self._bind_impl()
                if success:
                    self._is_bound = True
                    self._last_accessed = __import__('time').time()
                    log_buffer_operation("bound", self._get_buffer_info(), True)
                else:
                    log_buffer_operation("bound", self._get_buffer_info(), False, "binding failed")
                return success
            except Exception as e:
                log_buffer_operation("bound", self._get_buffer_info(), False, str(e))
                return False

    def unbind(self) -> bool:
        """Unbind the buffer.

        Returns:
            True if unbinding succeeded, False otherwise
        """
        from ornata.gpu.buffers.utils import log_buffer_operation
        with self._lock:
            try:
                if not self._is_bound:
                    return True  # Already unbound
                
                success = self._unbind_impl()
                if success:
                    self._is_bound = False
                    log_buffer_operation("unbound", self._get_buffer_info(), True)
                else:
                    log_buffer_operation("unbound", self._get_buffer_info(), False, "unbinding failed")
                return success
            except Exception as e:
                log_buffer_operation("unbound", self._get_buffer_info(), False, str(e))
                return False

    def cleanup(self) -> None:
        """Clean up GPU resources with proper error handling."""
        from ornata.gpu.buffers.utils import log_buffer_operation
        with self._lock:
            try:
                # Unbind if currently bound
                if self._is_bound:
                    self.unbind()
                
                # Release COM objects safely
                if self._com_object is not None:
                    from ornata.gpu.buffers.utils import safe_com_release
                    safe_com_release(self._com_object)
                    self._com_object = None
                
                # Cleanup GPU resources
                self._cleanup_impl()
                
                log_buffer_operation("cleaned up", self._get_buffer_info(), True)
                
            except Exception as e:
                log_buffer_operation("cleaned up", self._get_buffer_info(), False, str(e))

    def get_com_object(self) -> object | None:
        """Get COM object for DirectX operations."""
        return self._com_object

    def set_com_object(self, com_obj: object) -> None:
        """Set COM object for DirectX operations with ownership transfer."""
        with self._lock:
            if self._com_object is not None and self._com_object is not com_obj:
                # Release previous COM object
                from ornata.gpu.buffers.utils import safe_com_release
                safe_com_release(self._com_object)
            
            self._com_object = com_obj

    def _get_buffer_info(self) -> str:
        """Get formatted buffer information for logging."""
        from ornata.api.exports.definitions import RendererType
        from ornata.gpu.buffers.utils import format_buffer_info
        return format_buffer_info(
            buffer_type=self.__class__.__name__.lower().replace('buffer', ''),
            renderer=self._backend_kind or RendererType.CPU,
            usage=self._usage,
            size_bytes=self.buffer_size_bytes
        )

    @abstractmethod
    def _bind_impl(self) -> bool:
        """Backend-specific binding implementation.
        
        Returns:
            True if binding succeeded, False otherwise
        """
        pass

    @abstractmethod
    def _unbind_impl(self) -> bool:
        """Backend-specific unbinding implementation.
        
        Returns:
            True if unbinding succeeded, False otherwise
        """
        pass

    def _cleanup_impl(self) -> None:
        """Backend-specific cleanup implementation."""
        # Default implementation - subclasses can override
        self._buffer_id = None

    def __enter__(self):
        """Context manager entry."""
        self.bind()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.unbind()

    def __del__(self) -> None:
        """Destructor - ensure cleanup."""
        try:
            self.cleanup()
        except Exception:
            pass  # Avoid exceptions in destructor
