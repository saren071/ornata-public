"""GPU index buffer management."""

import ctypes
import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import RendererType
from ornata.api.exports.utils import get_logger
from ornata.gpu.buffers.base import GPUBuffer

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ornata.gpu.device.device import DeviceManager

logger = get_logger(__name__)


class IndexBuffer(GPUBuffer[int]):
    """GPU index buffer for storing vertex indices.

    Manages index data storage and GPU buffer operations with automatic
    fallback to CPU when GPU acceleration is unavailable.
    Supports DirectX and OpenGL renderers.
    """

    def __init__(self, indices: list[int], usage: str = "static", gpu_manager: DeviceManager | None = None) -> None:
        """Initialize index buffer with indices.

        Args:
            indices: List of vertex indices for indexed rendering.
            usage: Buffer usage pattern ('static', 'dynamic', 'stream').
            gpu_manager: Device manager instance for GPU operations.
        """
        super().__init__(indices, usage)
        self._index_count = len(indices)
        self._gpu_manager = gpu_manager
        self._buffer_id: int | None = None  # OpenGL buffer ID
        self._dx_buffer: Any | None = None  # DirectX buffer object
        self._dx_upload_data: Any | None = None  # Keep ctypes memory alive
        self._lock = threading.RLock()
        self._renderer_type: RendererType | None = None

        # Initialize GPU buffer if available
        self._create_gpu_buffer()

    @property
    def index_count(self) -> int:
        """Get the number of indices in the buffer."""
        return self._index_count

    @property
    def renderer_type(self):
        """Get the active renderer type."""
        return self._renderer_type

    def _create_gpu_buffer(self) -> None:
        """Create the GPU buffer if GPU acceleration is available."""
        with self._lock:
            if self._gpu_manager is None or not self._gpu_manager.is_available():
                return

            from ornata.api.exports.definitions import RendererType

            backend_kind = getattr(self._gpu_manager, "active_backend_kind", lambda: None)()
            
            if backend_kind == "directx":
                self._renderer_type = RendererType.DIRECTX11
                self._create_directx11_buffer()
            elif backend_kind == "opengl":
                self._renderer_type = RendererType.OPENGL
                self._create_opengl_buffer()
            else:
                self._renderer_type = RendererType.CPU
                logger.debug("No GPU renderer available, using CPU fallback")


    def _create_opengl_buffer(self) -> None:
        """Create OpenGL index buffer."""
        try:
            from ornata.api.exports.interop import GL_DYNAMIC_DRAW, GL_ELEMENT_ARRAY_BUFFER, GL_STATIC_DRAW, GL_STREAM_DRAW, GLuintArray, glBindBuffer, glBufferData, glGenBuffers

            # Generate buffer
            self._buffer_id = glGenBuffers(1)

            # Bind and upload data
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._buffer_id)

            # Convert data to appropriate format
            from ornata.api.exports.definitions import BufferUsage
            if self._usage == BufferUsage.STATIC:
                usage_flag = GL_STATIC_DRAW
            elif self._usage == BufferUsage.STREAM:
                usage_flag = GL_STREAM_DRAW
            else:  # dynamic
                usage_flag = GL_DYNAMIC_DRAW

            buffer_data = GLuintArray(self._data)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, buffer_data, usage_flag)

            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

            logger.debug(f"Created OpenGL index buffer with {self._index_count} indices")

        except Exception as e:
            logger.warning(f"Failed to create OpenGL index buffer: {e}")
            self._buffer_id = None

    def _create_directx11_buffer(self) -> None:
        """Create DirectX index buffer."""
        try:
            from ornata.api.exports.interop import (
                D3D11_BIND_INDEX_BUFFER,
                D3D11_BUFFER_DESC,
                D3D11_CPU_ACCESS_WRITE,
                D3D11_SUBRESOURCE_DATA,
                D3D11_USAGE_DYNAMIC,
                ID3D11Buffer,
            )

            if self._gpu_manager is None:
                raise RuntimeError("GPU manager is not initialized")
            if self._index_count == 0:
                raise ValueError("Index buffer requires at least one index")

            element_size = 4 if max(self._data) > 65535 else 2
            buffer_size = self._index_count * element_size

            buffer_desc = D3D11_BUFFER_DESC()
            buffer_desc.ByteWidth = buffer_size
            buffer_desc.Usage = D3D11_USAGE_DYNAMIC
            buffer_desc.BindFlags = D3D11_BIND_INDEX_BUFFER
            buffer_desc.CPUAccessFlags = D3D11_CPU_ACCESS_WRITE
            buffer_desc.MiscFlags = 0
            buffer_desc.StructureByteStride = element_size

            if element_size == 4:
                indices_array = (ctypes.c_uint32 * len(self._data))(*self._data)
            else:
                indices_array = (ctypes.c_uint16 * len(self._data))(*self._data)

            initial_data = D3D11_SUBRESOURCE_DATA()
            initial_data.pSysMem = ctypes.cast(indices_array, ctypes.c_void_p)
            initial_data.SysMemPitch = 0
            initial_data.SysMemSlicePitch = 0

            dx_buffer = ID3D11Buffer()
            result = self._gpu_manager.device.CreateBuffer(buffer_desc, initial_data, dx_buffer)
            if result != 0:
                raise RuntimeError(f"DirectX buffer creation failed: {result}")

            self._dx_buffer = dx_buffer
            self._dx_upload_data = indices_array
            self.set_com_object(dx_buffer)
            logger.debug(f"Created DirectX index buffer with {self._index_count} indices")

        except Exception as e:
            logger.warning(f"Failed to create DirectX index buffer: {e}")
            self._dx_buffer = None
            self._dx_upload_data = None

    def _bind_impl(self) -> bool:
        """Renderer-specific binding implementation.
        
        Returns:
            True if binding succeeded, False otherwise
        """
        try:
            if self._renderer_type == RendererType.DIRECTX11 and self._dx_buffer is not None:
                self._bind_directx11()
                return True
            elif self._renderer_type == RendererType.OPENGL and self._buffer_id is not None:
                self._bind_opengl()
                return True
            # CPU fallback - successful but no-op
            return True
        except Exception as e:
            logger.warning(f"Failed to bind index buffer: {e}")
            return False

    def _bind_directx11(self) -> None:
        """Bind DirectX11 index buffer."""
        try:
            from ornata.api.exports.interop import DXGI_FORMAT_R16_UINT, DXGI_FORMAT_R32_UINT
            
            # Determine format based on max index value
            element_size = 4 if max(self._data) > 65535 else 2
            format_constant = DXGI_FORMAT_R32_UINT if element_size == 4 else DXGI_FORMAT_R16_UINT
            
            if self._gpu_manager is None:
                raise RuntimeError("GPU manager is not initialized")
            self._gpu_manager.context.IASetIndexBuffer(self._dx_buffer, format_constant, 0)
            
        except Exception as e:
            logger.warning(f"Failed to bind DirectX index buffer: {e}")

    def _bind_opengl(self) -> None:
        """Bind OpenGL index buffer."""
        try:
            from ornata.api.exports.interop import GL_ELEMENT_ARRAY_BUFFER, glBindBuffer
            
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._buffer_id)
        except Exception as e:
            logger.warning(f"Failed to bind OpenGL index buffer: {e}")

    def _unbind_impl(self) -> bool:
        """Renderer-specific unbinding implementation.
        
        Returns:
            True if unbinding succeeded, False otherwise
        """
        try:
            if self._renderer_type == RendererType.DIRECTX11:
                self._unbind_directx11()
            elif self._renderer_type == RendererType.OPENGL:
                self._unbind_opengl()
            # CPU fallback - successful but no-op
            return True
        except Exception as e:
            logger.warning(f"Failed to unbind index buffer: {e}")
            return False

    def _unbind_directx11(self) -> None:
        """Unbind DirectX11 index buffer."""
        try:
            # DirectX doesn't require explicit unbind for index buffers
            pass
        except Exception as e:
            logger.warning(f"Failed to unbind DirectX index buffer: {e}")

    def _unbind_opengl(self) -> None:
        """Unbind OpenGL index buffer."""
        try:
            from ornata.api.exports.interop import GL_ELEMENT_ARRAY_BUFFER, glBindBuffer
            
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        except Exception as e:
            logger.warning(f"Failed to unbind OpenGL index buffer: {e}")

    def update_data(self, data: Sequence[int]) -> None:
        """Update buffer data.

        Args:
            data: New index data to upload to the buffer.
        """
        with self._lock:
            # Convert to list of ints for parent class
            super().update_data(list(data))
            self._index_count = len(data)

            # Update GPU buffer if available
            if self._renderer_type == RendererType.DIRECTX11 and self._dx_buffer is not None:
                self._update_directx11_buffer()
            elif self._renderer_type == RendererType.OPENGL and self._buffer_id is not None:
                self._update_opengl_buffer()

    def _update_directx11_buffer(self) -> None:
        """Update DirectX index buffer."""
        if self._dx_buffer is None:
            return

        try:
            import ctypes

            from ornata.api.exports.interop import D3D11_MAP_WRITE_DISCARD, D3D11_MAPPED_SUBRESOURCE
            
            # Create mapping
            mapped_resource = D3D11_MAPPED_SUBRESOURCE()
            if self._gpu_manager is None:
                raise RuntimeError("GPU manager is not initialized")
            result = self._gpu_manager.context.Map(
                self._dx_buffer, 0, D3D11_MAP_WRITE_DISCARD, 0, ctypes.byref(mapped_resource)
            )
            
            if result != 0:  # S_OK
                raise RuntimeError(f"DirectX index buffer mapping failed: {result}")
            
            element_size = 4 if max(self._data) > 65535 else 2
            if element_size == 4:
                indices_array = (ctypes.c_uint32 * len(self._data))(*self._data)
            else:
                indices_array = (ctypes.c_uint16 * len(self._data))(*self._data)

            ctypes.memmove(mapped_resource.pData, indices_array, len(self._data) * element_size)
            
            # Unmap
            self._gpu_manager.context.Unmap(self._dx_buffer, 0)
            
        except Exception as e:
            logger.warning(f"Failed to update DirectX index buffer: {e}")

    def _update_opengl_buffer(self) -> None:
        """Update OpenGL index buffer."""
        if self._buffer_id is None:
            return

        try:
            from ornata.api.exports.interop import GL_ELEMENT_ARRAY_BUFFER, GLuintArray, glBindBuffer, glBufferSubData

            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._buffer_id)
            buffer_data = GLuintArray(self._data)
            glBufferSubData(GL_ELEMENT_ARRAY_BUFFER, 0, buffer_data)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

        except Exception as e:
            logger.warning(f"Failed to update OpenGL index buffer: {e}")

    def _update_gpu_buffer_if_needed(self) -> None:
        """Update GPU buffer if buffer size has changed."""
        # Re-create GPU buffer with new size
        self._create_gpu_buffer()

    def cleanup(self) -> None:
        """Clean up GPU resources."""
        with self._lock:
            # Call parent cleanup
            super().cleanup()
            
            if self._renderer_type == RendererType.DIRECTX11 and self._dx_buffer is not None:
                self._cleanup_directx11()
            elif self._renderer_type == RendererType.OPENGL and self._buffer_id is not None:
                self._cleanup_opengl()

    def _cleanup_directx11(self) -> None:
        """Clean up DirectX resources."""
        try:
            from ornata.gpu.buffers.utils import safe_com_release

            if self._dx_buffer is not None:
                safe_com_release(self._dx_buffer)
                self._dx_buffer = None

            logger.debug("DirectX index buffer cleaned up")

        except Exception as e:
            logger.warning(f"Error cleaning up DirectX index buffer: {e}")

    def _cleanup_opengl(self) -> None:
        """Clean up OpenGL resources."""
        try:
            from ornata.api.exports.interop import GL_ELEMENT_ARRAY_BUFFER, glBindBuffer, glDeleteBuffers

            # Unbind if currently bound
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

            # Delete buffer
            glDeleteBuffers(1, [self._buffer_id])
            self._buffer_id = None

            logger.debug("OpenGL index buffer cleaned up")

        except Exception as e:
            logger.warning(f"Error cleaning up OpenGL index buffer: {e}")

    def __del__(self) -> None:
        """Destructor - ensure cleanup."""
        self.cleanup()
