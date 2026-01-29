"""GPU vertex buffer management."""

import ctypes
import threading
from typing import TYPE_CHECKING, Any, override

from ornata.api.exports.definitions import RendererType
from ornata.api.exports.utils import get_logger
from ornata.gpu.buffers.base import GPUBuffer

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ornata.gpu.device.device import DeviceManager

logger = get_logger(__name__)


class VertexBuffer(GPUBuffer[float]):
    """GPU vertex buffer for storing vertex data.

    Manages vertex data storage and GPU buffer operations with automatic
    fallback to CPU when GPU acceleration is unavailable.
    Supports DirectX and OpenGL renderers.
    """

    def __init__(self, data: list[float], usage: str = "static", stride_floats: int = 5, gpu_manager: DeviceManager | None = None) -> None:
        """Initialize vertex buffer with data.

        Args:
            data: List of vertex data (typically floats representing positions, normals, etc.)
            usage: Buffer usage pattern ('static', 'dynamic', 'stream')
            stride_floats: Number of floats per vertex (default 5: x, y, z, u, v)
            gpu_manager: GPU manager instance for GPU operations.
        """
        super().__init__(data, usage)
        self._stride_floats: int = max(1, int(stride_floats))
        self._vertex_count: int = len(data) // self._stride_floats
        self._gpu_manager = gpu_manager
        self._buffer_id: int | None = None  # OpenGL buffer ID
        self._dx_buffer: Any | None = None  # DirectX buffer object
        self._dx_input_layout: Any | None = None  # DirectX input layout
        self._dx_upload_data: Any | None = None  # Keeps ctypes data alive
        self._lock: threading.RLock = threading.RLock()
        self._renderer_kind: RendererType | None = None

        # Initialize GPU buffer if available
        self._create_gpu_buffer()

    @property
    def stride_floats(self) -> int:
        """Number of floats per vertex."""
        return self._stride_floats

    def set_stride(self, stride: int, data_length: int | None = None) -> None:
        """Update the stride and refresh vertex count for the buffer."""
        self._stride_floats = max(1, int(stride))
        data_length = len(self._data) if data_length is None else data_length
        self._vertex_count = max(1, data_length // self._stride_floats)

    @property
    def vertex_count(self) -> int:
        """Get the number of vertices in the buffer."""
        return self._vertex_count

    @property
    def renderer_kind(self) -> RendererType | None:
        """Get the active renderer kind."""
        return self._renderer_kind

    def _create_gpu_buffer(self) -> None:
        """Create the GPU buffer if GPU acceleration is available."""
        with self._lock:
            if self._gpu_manager is None or not self._gpu_manager.is_available():
                return
            
            # Detect active renderer
            backend_kind = getattr(self._gpu_manager, "active_backend_kind", lambda: None)()
            
            if backend_kind == "directx":
                self._renderer_kind = RendererType.DIRECTX11
                self._create_directx_buffer()
            elif backend_kind == "opengl":
                self._renderer_kind = RendererType.OPENGL
                self._create_opengl_buffer()
            else:
                # CPU fallback
                self._renderer_kind = RendererType.CPU
                logger.debug("No GPU renderer available, using CPU fallback")

    def _create_opengl_buffer(self) -> None:
        """Create OpenGL buffer."""
        try:
            # Attempt OpenGL path if available; otherwise noop (CPU fallback)
            from ornata.api.exports.interop import GL_ARRAY_BUFFER, GL_DYNAMIC_DRAW, GL_STATIC_DRAW, GL_STREAM_DRAW, glBindBuffer, glBufferData, glfloatArray, glGenBuffers
            from ornata.gpu.buffers.utils import BufferUsage
            # Generate buffer
            self._buffer_id = glGenBuffers(1)

            # Bind and upload data
            glBindBuffer(GL_ARRAY_BUFFER, self._buffer_id)

            # Convert data to appropriate format
            if self._usage == BufferUsage.STATIC:
                usage_flag = GL_STATIC_DRAW
            elif self._usage == BufferUsage.STREAM:
                usage_flag = GL_STREAM_DRAW
            else:  # dynamic
                usage_flag = GL_DYNAMIC_DRAW

            buffer_data = glfloatArray(self._data)
            glBufferData(GL_ARRAY_BUFFER, buffer_data, usage_flag)

            glBindBuffer(GL_ARRAY_BUFFER, 0)

            logger.debug(f"Created OpenGL vertex buffer with {self._vertex_count} vertices")

        except Exception as e:
            logger.warning(f"Failed to create OpenGL vertex buffer: {e}")
            self._buffer_id = None

    def _create_directx_buffer(self) -> None:
        """Create DirectX vertex buffer."""
        try:
            import ctypes

            from ornata.api.exports.interop import (
                D3D11_BIND_VERTEX_BUFFER,
                D3D11_BUFFER_DESC,
                D3D11_CPU_ACCESS_WRITE,
                D3D11_SUBRESOURCE_DATA,
                D3D11_USAGE_DYNAMIC,
                ID3D11Buffer,
            )

            if self._gpu_manager is None:
                raise RuntimeError("GPU manager is not initialized")
            if self._vertex_count == 0:
                raise ValueError("Vertex buffer requires at least one vertex")

            stride = self._stride_floats * 4  # 4 bytes per float
            buffer_size = self._vertex_count * stride

            buffer_desc = D3D11_BUFFER_DESC()
            buffer_desc.ByteWidth = buffer_size
            buffer_desc.Usage = D3D11_USAGE_DYNAMIC
            buffer_desc.BindFlags = D3D11_BIND_VERTEX_BUFFER
            buffer_desc.CPUAccessFlags = D3D11_CPU_ACCESS_WRITE
            buffer_desc.MiscFlags = 0
            buffer_desc.StructureByteStride = stride

            float_array = (ctypes.c_float * len(self._data))(*self._data)
            initial_data = D3D11_SUBRESOURCE_DATA()
            initial_data.pSysMem = ctypes.cast(float_array, ctypes.c_void_p)
            initial_data.SysMemPitch = 0
            initial_data.SysMemSlicePitch = 0

            dx_buffer = ID3D11Buffer()
            result = self._gpu_manager.device.CreateBuffer(buffer_desc, initial_data, dx_buffer)
            if result != 0:  # S_OK
                raise RuntimeError(f"DirectX buffer creation failed: {result}")

            self._dx_buffer = dx_buffer
            self._dx_upload_data = float_array
            self.set_com_object(dx_buffer)
            logger.debug(f"Created DirectX vertex buffer with {self._vertex_count} vertices")

        except Exception as e:
            logger.warning(f"Failed to create DirectX vertex buffer: {e}")
            self._dx_buffer = None
            self._dx_upload_data = None

    def _bind_impl(self) -> bool:
        """Renderer-specific binding implementation.
        
        Returns:
            True if binding succeeded, False otherwise
        """
        try:
            if self._renderer_kind == RendererType.DIRECTX11 and self._dx_buffer is not None:
                self._bind_directx()
                return True
            elif self._renderer_kind == RendererType.OPENGL and self._buffer_id is not None:
                self._bind_opengl()
                return True
            # CPU fallback - successful but no-op
            return True
        except Exception as e:
            logger.warning(f"Failed to bind vertex buffer: {e}")
            return False

    def _bind_directx(self) -> None:
        """Bind DirectX vertex buffer."""
        try:
            if self._gpu_manager is None:
                raise RuntimeError("GPU manager is not initialized")

            self._gpu_manager.context.IASetVertexBuffers(
                0,
                [self._dx_buffer],
                [self._stride_floats * 4],
                [0],
            )

            # Set input layout if available
            if self._dx_input_layout is not None:
                self._gpu_manager.context.IASetInputLayout(self._dx_input_layout)
                
        except Exception as e:
            logger.warning(f"Failed to bind DirectX vertex buffer: {e}")

    def _bind_opengl(self) -> None:
        """Bind OpenGL vertex buffer."""
        try:
            from ornata.api.exports.interop import GL_ARRAY_BUFFER, glBindBuffer

            glBindBuffer(GL_ARRAY_BUFFER, self._buffer_id)
        except Exception as e:
            logger.warning(f"Failed to bind OpenGL vertex buffer: {e}")

    def _unbind_impl(self) -> bool:
        """Renderer-specific unbinding implementation.
        
        Returns:
            True if unbinding succeeded, False otherwise
        """
        try:
            if self._renderer_kind == RendererType.DIRECTX11 and self._dx_buffer is not None:
                self._unbind_directx()
                return True
            elif self._renderer_kind == RendererType.OPENGL and self._buffer_id is not None:
                self._unbind_opengl()
                return True
            # CPU fallback - successful but no-op
            return True
        except Exception as e:
            logger.warning(f"Failed to unbind vertex buffer: {e}")
            return False

    def _unbind_directx(self) -> None:
        """Unbind DirectX vertex buffer."""
        try:
            if self._gpu_manager is None:
                raise RuntimeError("GPU manager is not initialized")
            # DirectX doesn't require explicit unbind, but we could reset the input layout
            if self._dx_input_layout is not None:
                self._gpu_manager.context.IASetInputLayout(None)
        except Exception as e:
            logger.warning(f"Failed to unbind DirectX vertex buffer: {e}")

    def _unbind_opengl(self) -> None:
        """Unbind OpenGL vertex buffer."""
        try:
            from ornata.api.exports.interop import GL_ARRAY_BUFFER, glBindBuffer

            glBindBuffer(GL_ARRAY_BUFFER, 0)
        except Exception as e:
            logger.warning(f"Failed to unbind OpenGL vertex buffer: {e}")

    def set_attribute_pointer(self, index: int, size: int, normalized: bool = False, stride: int = 0, offset: int = 0) -> None:
        """Set vertex attribute pointer for OpenGL renderer.

        Args:
            index: Attribute location index
            size: Number of components (1-4)
            normalized: Whether to normalize fixed-point values
            stride: Byte offset between consecutive vertex attributes
            offset: Byte offset of the first component
        """
        with self._lock:
            if self._renderer_kind != RendererType.OPENGL or self._buffer_id is None:
                return
                
            try:
                from ornata.api.exports.interop import GL_FLOAT, glEnableVertexAttribArray, glVertexAttribPointer

                glEnableVertexAttribArray(index)
                glVertexAttribPointer(
                    index, size, 
                    GL_FLOAT, 
                    normalized, 
                    stride if stride > 0 else self._stride_floats * 4, 
                    ctypes.c_void_p(offset)
                )
            except Exception as e:
                logger.warning(f"Failed to set vertex attribute pointer: {e}")

    def create_directx_input_layout(self, input_elements: list[dict[str, str | int]]) -> Any | None:
        """Create DirectX input layout for vertex attributes.

        Args:
            input_elements: List of input element descriptions with keys:
                          'semantic_name', 'semantic_index', 'format', 'input_slot', 'aligned_byte_offset'

        Returns:
            DirectX input layout object or None if creation fails
        """
        if self._renderer_kind != RendererType.DIRECTX11 or self._gpu_manager is None:
            return None
            
        try:
            import ctypes

            from ornata.api.exports.interop import D3D11_INPUT_ELEMENT_DESC, D3D11_INPUT_PER_VERTEX_DATA, DXGI_FORMAT_R32G32B32A32_FLOAT
            
            # Create input element descriptions
            num_elements = len(input_elements)
            elements_array = (D3D11_INPUT_ELEMENT_DESC * num_elements)()
            
            for i, element in enumerate(input_elements):
                elem = D3D11_INPUT_ELEMENT_DESC()
                semantic_name_value = element.get('semantic_name', '')
                elem.SemanticName = str(semantic_name_value).encode('utf-8')
                elem.SemanticIndex = int(element.get('semantic_index', 0))
                elem.Format = element.get('format', DXGI_FORMAT_R32G32B32A32_FLOAT)
                elem.InputSlot = int(element.get('input_slot', 0))
                elem.AlignedByteOffset = int(element.get('aligned_byte_offset', i * 16))
                elem.InputSlotClass = D3D11_INPUT_PER_VERTEX_DATA
                elem.InstanceDataStepRate = 0
                elements_array[i] = elem
            
            # Create input layout
            from ornata.api.exports.interop import ID3D11InputLayout
            layout = ID3D11InputLayout()
            result = self._gpu_manager.device.CreateInputLayout(
                elements_array,
                num_elements,
                ctypes.c_void_p(),
                0,
                layout
            )
            
            if result != 0:  # S_OK
                raise RuntimeError(f"DirectX input layout creation failed: {result}")
                
            self._dx_input_layout = layout
            logger.debug(f"Created DirectX input layout with {num_elements} elements")
            return self._dx_input_layout
            
        except Exception as e:
            logger.warning(f"Failed to create DirectX input layout: {e}")
            return None

    @override
    def update_data(self, data: Sequence[float]) -> None:
        """Update buffer data.

        Args:
            data: New vertex data to upload to the buffer.
        """
        with self._lock:
            super().update_data(data)
            self._vertex_count = len(data) // self._stride_floats

            # Update GPU buffer if available
            if self._renderer_kind == RendererType.DIRECTX11 and self._dx_buffer is not None:
                self._update_directx_buffer()
            elif self._renderer_kind == RendererType.OPENGL and self._buffer_id is not None:
                self._update_opengl_buffer()

    def _update_directx_buffer(self) -> None:
        """Update DirectX vertex buffer."""
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
                raise RuntimeError(f"DirectX buffer mapping failed: {result}")
            
            # Copy data to mapped buffer using contiguous array to avoid invalid pointers
            float_array = (ctypes.c_float * len(self._data))(*self._data)
            ctypes.memmove(mapped_resource.pData, float_array, len(self._data) * 4)
            
            # Unmap
            self._gpu_manager.context.Unmap(self._dx_buffer, 0)
            
        except Exception as e:
            logger.warning(f"Failed to update DirectX vertex buffer: {e}")

    def _update_opengl_buffer(self) -> None:
        """Update OpenGL vertex buffer."""
        if self._buffer_id is None:
            return

        try:
            from ornata.api.exports.interop import GL_ARRAY_BUFFER, glBindBuffer, glBufferSubData, glfloatArray

            glBindBuffer(GL_ARRAY_BUFFER, self._buffer_id)
            buffer_data = glfloatArray(self._data)
            glBufferSubData(GL_ARRAY_BUFFER, 0, buffer_data)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
        except Exception as e:
            logger.warning(f"Failed to update OpenGL vertex buffer: {e}")

    def update_sub_data(self, offset: int, data: list[float]) -> None:
        """Update a portion of the buffer data efficiently.

        Args:
            offset: Starting vertex index to update.
            data: New vertex data to upload.
        """
        with self._lock:
            if offset < 0 or offset >= self._vertex_count:
                raise ValueError(f"Invalid offset {offset} for buffer with {self._vertex_count} vertices")

            data_vertices = len(data) // self._stride_floats
            if offset + data_vertices > self._vertex_count:
                raise ValueError("Data would exceed buffer bounds")

            # Update CPU data
            start_idx = offset * self._stride_floats
            end_idx = start_idx + len(data)
            self._data[start_idx:end_idx] = data

            # Update GPU buffer if available
            if self._renderer_kind == RendererType.DIRECTX11 and self._dx_buffer is not None:
                self._update_directx_sub_data(start_idx * 4, data)  # *4 for float size
            elif self._renderer_kind == RendererType.OPENGL and self._buffer_id is not None:
                self._update_opengl_sub_data(start_idx * 4, data)

    def _update_directx_sub_data(self, byte_offset: int, data: list[float]) -> None:
        """Update a portion of the DirectX buffer efficiently."""
        if self._dx_buffer is None:
            return

        try:
            # For simplicity, update the entire buffer for sub-data updates
            # In a more optimized implementation, we would use partial mapping
            self._update_directx_buffer()
        except Exception as e:
            logger.warning(f"Failed to update DirectX vertex buffer sub-data: {e}")

    def _update_opengl_sub_data(self, byte_offset: int, data: list[float]) -> None:
        """Update a portion of the OpenGL buffer efficiently."""
        if self._buffer_id is None:
            return

        try:
            from ornata.api.exports.interop import GL_ARRAY_BUFFER, glBindBuffer, glBufferSubData, glfloatArray

            glBindBuffer(GL_ARRAY_BUFFER, self._buffer_id)
            buffer_data = glfloatArray(data)
            glBufferSubData(GL_ARRAY_BUFFER, byte_offset, buffer_data)
            glBindBuffer(GL_ARRAY_BUFFER, 0)

        except Exception as e:
            logger.warning(f"Failed to update OpenGL vertex buffer sub-data: {e}")

    def cleanup(self) -> None:
        """Clean up GPU resources."""
        with self._lock:
            if self._renderer_kind == RendererType.DIRECTX11 and self._dx_buffer is not None:
                self._cleanup_directx()
            elif self._renderer_kind == RendererType.OPENGL and self._buffer_id is not None:
                self._cleanup_opengl()

    def _cleanup_directx(self) -> None:
        """Clean up DirectX resources."""
        try:
            from ornata.gpu.buffers.utils import safe_com_release

            if self._dx_input_layout is not None:
                safe_com_release(self._dx_input_layout)
                self._dx_input_layout = None

            if self._dx_buffer is not None:
                safe_com_release(self._dx_buffer)
                self._dx_buffer = None

            logger.debug("DirectX vertex buffer cleaned up")

        except Exception as e:
            logger.warning(f"Error cleaning up DirectX vertex buffer: {e}")

    def _cleanup_opengl(self) -> None:
        """Clean up OpenGL resources."""
        try:
            from ornata.api.exports.interop import GL_ARRAY_BUFFER, glBindBuffer, glDeleteBuffers

            # Unbind if currently bound
            glBindBuffer(GL_ARRAY_BUFFER, 0)

            # Delete buffer
            glDeleteBuffers(1, [self._buffer_id])
            self._buffer_id = None

            logger.debug("OpenGL vertex buffer cleaned up")

        except Exception as e:
            logger.warning(f"Error cleaning up OpenGL vertex buffer: {e}")

    @override
    def _update_gpu_buffer_if_needed(self) -> None:
        """Update GPU buffer when size has changed.
        
        This method is called when the buffer size changes and ensures
        the GPU buffer is recreated with the new data for all supported renderers.
        """
        with self._lock:
            try:
                # Clean up existing GPU resources
                self.cleanup()
                
                # Update vertex count based on new data size
                old_vertex_count = self._vertex_count
                self._vertex_count = len(self._data) // self._stride_floats
                
                # Recreate GPU buffer if GPU manager is available
                if self._gpu_manager is not None and self._gpu_manager.is_available():
                    self._create_gpu_buffer()
                    
                    # Log the update
                    logger.debug(f"Updated vertex buffer: {old_vertex_count} -> {self._vertex_count} vertices")
                else:
                    logger.debug("GPU not available, using CPU fallback after size change")
                    
            except Exception as e:
                logger.warning(f"Failed to update GPU vertex buffer after size change: {e}")

    def __del__(self) -> None:
        """Destructor - ensure cleanup."""
        self.cleanup()
