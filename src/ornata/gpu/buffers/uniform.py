"""GPU uniform buffer management."""

import ctypes
import threading
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import RendererType
from ornata.api.exports.utils import get_logger
from ornata.gpu.buffers.base import GPUBuffer

if TYPE_CHECKING:
    from ornata.gpu.device.device import DeviceManager

logger = get_logger(__name__)

UniformValue = float | int | Sequence[float]


class UniformBuffer(GPUBuffer[float]):
    """GPU uniform buffer for storing shader uniform data.

    Supports DirectX11 and OpenGL renderers with proper std140 layout support.
    """

    def __init__(self, data: dict[str, UniformValue], usage: str = "dynamic", gpu_manager: DeviceManager | None = None) -> None:
        """Initialize uniform buffer with data.

        Args:
            data: Dictionary mapping uniform names to values
            usage: Buffer usage pattern ('static', 'dynamic', 'stream')
            gpu_manager: GPU manager instance for GPU operations.
        """
        # Pack data into structured format for GPU
        structured_data = self._pack_uniform_data(data)
        super().__init__(structured_data, usage)
        self._uniform_layout: dict[str, UniformValue] = data.copy()
        self._gpu_manager = gpu_manager
        self._buffer_id: int | None = None  # OpenGL buffer ID
        self._dx11_buffer: Any | None = None  # DirectX11 buffer object
        self._lock = threading.RLock()
        self._bound_slot: int | None = None
        self._renderer_type: RendererType | None = None

        # Initialize GPU buffer if available
        self._create_gpu_buffer()

    def _pack_uniform_data(self, data: dict[str, UniformValue]) -> list[float]:
        """Pack uniform data into a format suitable for GPU buffers.

        Handles different data types with proper alignment and padding for std140 layout.

        Args:
            data: Dictionary of uniform data

        Returns:
            Packed float data for GPU buffer
        """
        packed: list[float] = []

        for key, value in data.items():
            if isinstance(value, (int, float)):
                # Scalar values - pad to vec4 alignment
                packed.extend([float(value), 0.0, 0.0, 0.0])
            else:
                if len(value) == 2:
                    # vec2 - pad to vec4
                    packed.extend([float(value[0]), float(value[1]), 0.0, 0.0])
                elif len(value) == 3:
                    # vec3 - pad to vec4
                    packed.extend([float(value[0]), float(value[1]), float(value[2]), 0.0])
                elif len(value) == 4:
                    # vec4 - no padding needed
                    packed.extend(float(v) for v in value)
                elif len(value) == 9:
                    # mat3 - treat as 3 vec4 rows
                    packed.extend(
                        [
                            float(value[0]),
                            float(value[1]),
                            float(value[2]),
                            0.0,  # row 0
                            float(value[3]),
                            float(value[4]),
                            float(value[5]),
                            0.0,  # row 1
                            float(value[6]),
                            float(value[7]),
                            float(value[8]),
                            0.0,  # row 2
                        ]
                    )
                elif len(value) == 16:
                    # mat4 - treat as 4 vec4 rows
                    packed.extend(float(v) for v in value)
                else:
                    raise ValueError(f"Unsupported uniform array length for {key}: {len(value)}")

        return packed

    @property
    def renderer_type(self) -> RendererType | None:
        """Get the active renderer type."""
        return self._renderer_type

    def _create_gpu_buffer(self) -> None:
        """Create the GPU buffer if GPU acceleration is available."""
        with self._lock:
            if self._gpu_manager is None or not self._gpu_manager.is_available():
                return
            
            # Detect active renderer
            backend_kind = getattr(self._gpu_manager, "active_backend_kind", lambda: None)()
            
            if backend_kind == "directx":
                self._renderer_type = RendererType.DIRECTX11
                self._create_directx11_buffer()
            elif backend_kind == "opengl":
                self._renderer_type = RendererType.OPENGL
                self._create_opengl_buffer()
            else:
                # CPU fallback
                self._renderer_type = RendererType.CPU
                logger.debug("No GPU renderer available, using CPU fallback")

    def _create_opengl_buffer(self) -> None:
        """Create OpenGL uniform buffer."""
        try:
            # Create uniform buffer object if OpenGL is available
            from ornata.api.exports.interop import GL_DYNAMIC_DRAW, GL_STATIC_DRAW, GL_STREAM_DRAW, GL_UNIFORM_BUFFER, glBindBuffer, glBufferData, glfloatArray, glGenBuffers

            # Generate buffer
            self._buffer_id = glGenBuffers(1)

            # Bind and upload data
            glBindBuffer(GL_UNIFORM_BUFFER, self._buffer_id)

            # Convert data to appropriate format
            from ornata.gpu.buffers.utils import BufferUsage
            if self._usage == BufferUsage.STATIC:
                usage_flag = GL_STATIC_DRAW
            elif self._usage == BufferUsage.STREAM:
                usage_flag = GL_STREAM_DRAW
            else:  # dynamic
                usage_flag = GL_DYNAMIC_DRAW

            buffer_data = glfloatArray(self._data)
            glBufferData(GL_UNIFORM_BUFFER, buffer_data, usage_flag)

            glBindBuffer(GL_UNIFORM_BUFFER, 0)

            logger.debug(f"Created OpenGL uniform buffer with {len(self._data)} floats")

        except Exception as e:
            logger.warning(f"Failed to create OpenGL uniform buffer: {e}")
            self._buffer_id = None

    def _create_directx11_buffer(self) -> None:
        """Create DirectX11 uniform buffer."""
        try:
            from ornata.api.exports.interop import (
                D3D11_BIND_CONSTANT_BUFFER,
                D3D11_BUFFER_DESC,
                D3D11_CPU_ACCESS_WRITE,
                D3D11_SUBRESOURCE_DATA,
                D3D11_USAGE_DYNAMIC,
                ID3D11Buffer,
            )

            # Create uniform buffer description
            buffer_size = len(self._data) * 4  # 4 bytes per float
            
            # Setup buffer description for dynamic usage
            buffer_desc = D3D11_BUFFER_DESC()
            buffer_desc.ByteWidth = buffer_size
            buffer_desc.Usage = D3D11_USAGE_DYNAMIC
            buffer_desc.BindFlags = D3D11_BIND_CONSTANT_BUFFER
            buffer_desc.CPUAccessFlags = D3D11_CPU_ACCESS_WRITE
            buffer_desc.MiscFlags = 0

            # Setup initial data
            initial_data = D3D11_SUBRESOURCE_DATA()

            # Convert Python float array to ctypes array
            float_array = (ctypes.c_float * len(self._data))(*self._data)
            initial_data.pSysMem = ctypes.cast(float_array, ctypes.c_void_p)

            # Create buffer via the high-level wrapper
            if self._gpu_manager is None:
                raise RuntimeError("GPU manager is not initialized")

            dx_buffer = ID3D11Buffer()
            result = self._gpu_manager.device.CreateBuffer(buffer_desc, initial_data, dx_buffer)

            if result != 0:  # S_OK
                raise RuntimeError(f"DirectX11 uniform buffer creation failed: {result}")

            self._dx11_buffer = dx_buffer
            logger.debug(f"Created DirectX11 uniform buffer with {len(self._data)} floats")

        except Exception as e:
            logger.warning(f"Failed to create DirectX11 uniform buffer: {e}")
            self._dx11_buffer = None

    def update_uniform(self, name: str, value: UniformValue) -> None:
        """Update a specific uniform value.

        Args:
            name: Name of the uniform to update
            value: New value for the uniform

        Raises:
            ValueError: If uniform name not found or invalid value type
        """
        with self._lock:
            if name not in self._uniform_layout:
                raise ValueError(f"Uniform '{name}' not found in buffer layout")

            # Update layout
            self._uniform_layout[name] = value

            # Re-pack all data
            self._data = self._pack_uniform_data(self._uniform_layout)

            # Update GPU buffer if available
            from ornata.api.exports.definitions import RendererType
            if self._renderer_type == RendererType.DIRECTX11 and self._dx11_buffer is not None:
                self._update_directx11_buffer()
            elif self._renderer_type == RendererType.OPENGL and self._buffer_id is not None:
                self._update_opengl_buffer()

    def _update_directx11_buffer(self) -> None:
        """Update DirectX11 uniform buffer."""
        if self._dx11_buffer is None:
            return

        try:
            import ctypes

            from ornata.api.exports.interop import D3D11_MAP_WRITE_DISCARD, D3D11_MAPPED_SUBRESOURCE

            # Create mapping
            mapped_resource = D3D11_MAPPED_SUBRESOURCE()
            if self._gpu_manager is None:
                raise RuntimeError("GPU manager is not initialized")
            result = self._gpu_manager.context.Map(
                self._dx11_buffer, 0, D3D11_MAP_WRITE_DISCARD, 0, ctypes.byref(mapped_resource)
            )

            if result != 0:  # S_OK
                raise RuntimeError(f"DirectX11 uniform buffer mapping failed: {result}")

            # Copy data to mapped buffer using a contiguous ctypes float array
            float_array = (ctypes.c_float * len(self._data))(*self._data)
            ctypes.memmove(mapped_resource.pData, float_array, len(self._data) * 4)

            # Unmap
            self._gpu_manager.context.Unmap(self._dx11_buffer, 0)

        except Exception as e:
            logger.warning(f"Failed to update DirectX11 uniform buffer: {e}")

    def _update_opengl_buffer(self) -> None:
        """Update OpenGL uniform buffer."""
        if self._buffer_id is None:
            return

        try:
            from ornata.api.exports.interop import GL_UNIFORM_BUFFER, glBindBuffer, glBufferSubData, glfloatArray

            glBindBuffer(GL_UNIFORM_BUFFER, self._buffer_id)
            buffer_data = glfloatArray(self._data)
            glBufferSubData(GL_UNIFORM_BUFFER, 0, buffer_data)
            glBindBuffer(GL_UNIFORM_BUFFER, 0)

        except Exception as e:
            logger.warning(f"Failed to update OpenGL uniform buffer: {e}")

    def _bind_impl(self) -> bool:
        """Renderer-specific binding implementation.
        
        Returns:
            True if binding succeeded, False otherwise
        """
        try:
            from ornata.api.exports.definitions import RendererType
            if self._renderer_type == RendererType.DIRECTX11 and self._dx11_buffer is not None:
                # Use slot 0 by default for binding
                self._bind_directx11(0)
                return True
            elif self._renderer_type == RendererType.OPENGL and self._buffer_id is not None:
                # Use slot 0 by default for binding
                self._bind_opengl(0)
                return True
            else:
                # CPU fallback - successful but no-op
                self._bound_slot = 0
                return True
        except Exception as e:
            logger.warning(f"Failed to bind uniform buffer: {e}")
            return False

    def _bind_directx11(self, slot: int) -> None:
        """Bind DirectX11 uniform buffer."""
        try:
            import ctypes
            
            # DirectX11 constant buffer array
            buffers_array = (ctypes.c_void_p * 1)(self._dx11_buffer)
            counts_array = (ctypes.c_uint32 * 1)(1)
            offsets_array = (ctypes.c_uint32 * 1)(0)
            
            # VSSetConstantBuffers1 for vertex shader constants
            if self._gpu_manager is None:
                raise RuntimeError("GPU manager is not initialized")
            self._gpu_manager.context.VSSetConstantBuffers1(slot, 1, buffers_array, offsets_array, counts_array)
            
            # PSSetConstantBuffers1 for pixel shader constants
            self._gpu_manager.context.PSSetConstantBuffers1(slot, 1, buffers_array, offsets_array, counts_array)
            
            self._bound_slot = slot
            
        except Exception as e:
            logger.warning(f"Failed to bind DirectX11 uniform buffer: {e}")

    def _bind_opengl(self, slot: int) -> None:
        """Bind OpenGL uniform buffer."""
        try:
            from ornata.api.exports.interop import GL_UNIFORM_BUFFER, glBindBufferBase

            glBindBufferBase(GL_UNIFORM_BUFFER, slot, self._buffer_id)
            self._bound_slot = slot

        except Exception as e:
            logger.warning(f"Failed to bind OpenGL uniform buffer: {e}")

    def unbind(self) -> bool:
        """Unbind the uniform buffer.

        Returns:
            True if unbinding succeeded.
        """
        with self._lock:
            from ornata.api.exports.definitions import RendererType
            if self._renderer_type == RendererType.DIRECTX11:
                self._unbind_directx11()
            elif self._renderer_type == RendererType.OPENGL:
                self._unbind_opengl()
            else:
                self._bound_slot = None
            return True

    def _unbind_directx11(self) -> None:
        """Unbind DirectX11 uniform buffer."""
        try:
            import ctypes
            
            # Unbind by setting null buffers
            if self._bound_slot is not None:
                buffers_array = (ctypes.c_void_p * 1)(None)
                counts_array = (ctypes.c_uint32 * 1)(0)
                offsets_array = (ctypes.c_uint32 * 1)(0)
                
                if self._gpu_manager is None:
                    raise RuntimeError("GPU manager is not initialized")
                self._gpu_manager.context.VSSetConstantBuffers1(self._bound_slot, 1, buffers_array, offsets_array, counts_array)
                self._gpu_manager.context.PSSetConstantBuffers1(self._bound_slot, 1, buffers_array, offsets_array, counts_array)
                
                self._bound_slot = None
            
        except Exception as e:
            logger.warning(f"Failed to unbind DirectX11 uniform buffer: {e}")

    def _unbind_opengl(self) -> None:
        """Unbind OpenGL uniform buffer."""
        try:
            from ornata.api.exports.interop import GL_UNIFORM_BUFFER, glBindBufferBase

            if self._bound_slot is not None:
                glBindBufferBase(GL_UNIFORM_BUFFER, self._bound_slot, 0)
                self._bound_slot = None

        except Exception as e:
            logger.warning(f"Failed to unbind OpenGL uniform buffer: {e}")

    def _update_gpu_buffer_if_needed(self) -> None:
        """Update GPU buffer if buffer size has changed."""
        # Uniform buffer doesn't support dynamic resizing in the same way
        # as other buffer types. For now, just recreate the GPU buffer
        # if the renderer has changed or if GPU manager is available.
        self.cleanup()
        self._create_gpu_buffer()

    def cleanup(self) -> None:
        """Clean up GPU resources."""
        with self._lock:
            from ornata.api.exports.definitions import RendererType
            if self._renderer_type == RendererType.DIRECTX11 and self._dx11_buffer is not None:
                self._cleanup_directx11()
            elif self._renderer_type == RendererType.OPENGL and self._buffer_id is not None:
                self._cleanup_opengl()

    def _cleanup_directx11(self) -> None:
        """Clean up DirectX11 resources."""
        try:
            # Unbind if currently bound
            if self._bound_slot is not None:
                self._unbind_directx11()
                
            if self._dx11_buffer is not None:
                self._dx11_buffer.Release()
                self._dx11_buffer = None
                
            logger.debug("DirectX11 uniform buffer cleaned up")

        except Exception as e:
            logger.warning(f"Error cleaning up DirectX11 uniform buffer: {e}")

    def _cleanup_opengl(self) -> None:
        """Clean up OpenGL resources."""
        try:
            from ornata.api.exports.interop import GL_UNIFORM_BUFFER, glBindBufferBase, glDeleteBuffers

            # Unbind if currently bound
            if self._bound_slot is not None:
                glBindBufferBase(GL_UNIFORM_BUFFER, self._bound_slot, 0)
                self._bound_slot = None

            # Delete buffer
            if self._buffer_id is not None:
                glDeleteBuffers(1, [self._buffer_id])
                self._buffer_id = None

            logger.debug("OpenGL uniform buffer cleaned up")

        except Exception as e:
            logger.warning(f"Error cleaning up OpenGL uniform buffer: {e}")

    def __del__(self) -> None:
        """Destructor - ensure cleanup."""
        self.cleanup()
