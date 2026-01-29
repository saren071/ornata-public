# ===========================
# ornata/gpu/backends/directx/device.py
# ===========================
"""DirectX device management module.

Creates a D3D11 device (hardware preferred, WARP fallback) and exposes:
- native_device  -> ID3D11Device
- native_context -> ID3D11DeviceContext
- feature_level  -> chosen D3D_FEATURE_LEVEL
- helper buffer creation via DirectXBufferManager
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.interop import D3D_FEATURE_LEVEL, ID3D11Buffer, ID3D11Device, ID3D11DeviceContext

logger = get_logger(__name__)


class DirectXDevice:
    """Manages DirectX device creation and management."""

    def __init__(self) -> None:
        self._device: ID3D11Device | None = None
        self._context: ID3D11DeviceContext | None = None
        self._feature_level: D3D_FEATURE_LEVEL | None = None
        self._buffer_manager = None
        self._initialized = False
        self._initialize_device()

    def _initialize_device(self) -> None:
        """Create the D3D11 device and initialize helpers."""
        from ornata.api.exports.interop import D3D11_CREATE_DEVICE_BGRA_SUPPORT, D3D11_SDK_VERSION, D3D_DRIVER_TYPE, D3D_FEATURE_LEVEL, D3D11CreateDevice

        feature_levels: list[int] = [
            D3D_FEATURE_LEVEL.LEVEL_11_1,
            D3D_FEATURE_LEVEL.LEVEL_11_0,
            D3D_FEATURE_LEVEL.LEVEL_10_1,
            D3D_FEATURE_LEVEL.LEVEL_10_0,
        ]
        flags = D3D11_CREATE_DEVICE_BGRA_SUPPORT

        hr, device_ptr, chosen_level, context_ptr = D3D11CreateDevice(
            None,
            D3D_DRIVER_TYPE.HARDWARE,
            None,
            flags,
            feature_levels,
            D3D11_SDK_VERSION,
        )

        if hr != 0:
            logger.debug(f"D3D11CreateDevice(HARDWARE) failed hr={hr}; retrying with WARP")
            hr, device_ptr, chosen_level, context_ptr = D3D11CreateDevice(
                None,
                D3D_DRIVER_TYPE.WARP,
                None,
                flags,
                feature_levels,
                D3D11_SDK_VERSION,
            )
            if hr != 0:
                raise RuntimeError(f"D3D11CreateDevice failed: hr={hr}")

        self._device = device_ptr
        self._context = context_ptr
        self._feature_level = chosen_level

        # Initialize buffer manager (re-exported through API exports in this project)
        from ornata.api.exports.gpu import DirectXBufferManager

        self._buffer_manager = DirectXBufferManager(self._device)
        self._initialized = True
        logger.debug("DirectX device initialized successfully")

    def create_vertex_buffer(self, vertices: list[float]) -> ID3D11Buffer:
        """Create a vertex buffer from vertex data."""
        if self._buffer_manager is None:
            raise RuntimeError("Buffer manager is not initialized")
        return self._buffer_manager.create_vertex_buffer(vertices)

    def create_index_buffer(self, indices: list[int]) -> ID3D11Buffer:
        """Create an index buffer from index data."""
        if self._buffer_manager is None:
            raise RuntimeError("Buffer manager is not initialized")
        return self._buffer_manager.create_index_buffer(indices)

    def create_instance_buffer(self, instance_data: list[float]) -> ID3D11Buffer:
        """Create an instance buffer from instance transform data."""
        if self._buffer_manager is None:
            raise RuntimeError("Buffer manager is not initialized")
        return self._buffer_manager.create_instance_buffer(instance_data)

    @property
    def native_device(self) -> ID3D11Device | None:
        """The underlying ID3D11Device COM wrapper."""
        return self._device

    @property
    def native_context(self) -> ID3D11DeviceContext | None:
        """The underlying immediate context."""
        return self._context

    @property
    def feature_level(self) -> D3D_FEATURE_LEVEL | None:
        """The chosen D3D feature level."""
        return self._feature_level

    def cleanup(self) -> None:
        """Mark the device wrapper as no longer initialized."""
        self._initialized = False