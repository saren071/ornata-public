# ===========================
# ornata/gpu/backends/directx/buffer_manager.py
# ===========================
"""DirectX buffer management module.

Creates immutable/default-usage vertex, index, and instance buffers. All paths
are real and raise on failure; no simulated or placeholder objects are returned.
"""

from __future__ import annotations

import ctypes
from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.interop import ID3D11Buffer, ID3D11Device

logger = get_logger(__name__)


class DirectXBufferManager:
    """Manages creation of D3D11 buffers."""

    def __init__(self, device: ID3D11Device) -> None:
        """Initialize with a valid `ID3D11Device`."""
        self._device = device
        self._initialized = True

    def _create_buffer(self, bind_flags: int, data_ptr: int, byte_count: int) -> ID3D11Buffer:
        from ornata.api.exports.interop import D3D11_BUFFER_DESC, D3D11_SUBRESOURCE_DATA, D3D11_USAGE_DEFAULT, ID3D11Buffer

        bd = D3D11_BUFFER_DESC()
        bd.ByteWidth = int(byte_count)
        bd.Usage = D3D11_USAGE_DEFAULT
        bd.BindFlags = int(bind_flags)
        bd.CPUAccessFlags = 0
        bd.MiscFlags = 0
        bd.StructureByteStride = 0

        init_data = D3D11_SUBRESOURCE_DATA()
        init_data.pSysMem = ctypes.c_void_p(data_ptr)
        init_data.SysMemPitch = 0
        init_data.SysMemSlicePitch = 0

        out = ID3D11Buffer()
        hr: int = self._device.CreateBuffer(bd, init_data, out)
        if hr != 0:
            raise RuntimeError(f"CreateBuffer failed: hr={hr}")
        return out

    def create_vertex_buffer(self, vertices: list[float]) -> ID3D11Buffer:
        """Create a vertex buffer from interleaved floats."""
        if not self._initialized:
            raise RuntimeError("DirectXBufferManager not initialized")
        if not vertices:
            raise ValueError("Vertices list cannot be empty")
        from ornata.api.exports.interop import D3D11_BIND_VERTEX_BUFFER

        data_array = (ctypes.c_float * len(vertices))(*[float(v) for v in vertices])
        return self._create_buffer(D3D11_BIND_VERTEX_BUFFER, ctypes.addressof(data_array), len(vertices) * 4)

    def create_index_buffer(self, indices: list[int]) -> ID3D11Buffer:
        """Create an index buffer from uint32 indices."""
        if not self._initialized:
            raise RuntimeError("DirectXBufferManager not initialized")
        if not indices:
            raise ValueError("Indices list cannot be empty")
        from ornata.api.exports.interop import D3D11_BIND_INDEX_BUFFER

        data_array = (ctypes.c_uint * len(indices))(*[int(i) for i in indices])
        return self._create_buffer(D3D11_BIND_INDEX_BUFFER, ctypes.addressof(data_array), len(indices) * 4)

    def create_instance_buffer(self, instance_data: list[float]) -> ID3D11Buffer:
        """Create an instance buffer (per-instance data)."""
        if not self._initialized:
            raise RuntimeError("DirectXBufferManager not initialized")
        if not instance_data:
            raise ValueError("Instance data cannot be empty")
        from ornata.api.exports.interop import D3D11_BIND_VERTEX_BUFFER

        data_array = (ctypes.c_float * len(instance_data))(*[float(v) for v in instance_data])
        return self._create_buffer(D3D11_BIND_VERTEX_BUFFER, ctypes.addressof(data_array), len(instance_data) * 4)
