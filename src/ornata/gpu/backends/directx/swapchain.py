# ===========================
# ornata/gpu/backends/directx/swap_chain.py
# ===========================
"""DirectX swap chain management module.

This module creates a DXGI swap chain for presentation **when provided a window
handle (HWND)**. Since the Ornata D3D11 backend primarily renders offscreen
to an RTV, a swap chain is optional. No simulated objects are returned.

Usage:
    swap = DirectXSwapChain(device, hwnd)
    swap.present()

If `hwnd` is omitted or invalid, initialization raises an error.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.interop import ID3D11Device, IDXGISwapChain

logger = get_logger(__name__)


class DirectXSwapChain:
    """Manages a DXGI swap chain for presentation."""

    def __init__(self, device: ID3D11Device | None, hwnd: int | None) -> None:
        if device is None:
            raise ValueError("DirectXSwapChain requires a valid ID3D11Device")
        if hwnd is None or hwnd == 0:
            raise ValueError("DirectXSwapChain requires a valid window handle (HWND)")
        self._device = device
        self._hwnd = hwnd
        self._swap_chain: IDXGISwapChain | None = None
        self._initialized = False
        self._initialize_swap_chain()

    def _initialize_swap_chain(self) -> None:
        # Create DXGI factory
        from ornata.api.exports.interop import CreateDXGIFactory
        dxgi_factory = CreateDXGIFactory()

        # Swap chain description
        from ornata.api.exports.interop import DXGI_SWAP_CHAIN_DESC
        desc = DXGI_SWAP_CHAIN_DESC()
        desc.BufferDesc.Width = 800
        desc.BufferDesc.Height = 600
        desc.BufferDesc.RefreshRate.Numerator = 60
        desc.BufferDesc.RefreshRate.Denominator = 1
        from ornata.api.exports.interop import DXGI_FORMAT_R8G8B8A8_UNORM
        desc.BufferDesc.Format = DXGI_FORMAT_R8G8B8A8_UNORM
        from ornata.api.exports.interop import DXGI_MODE_SCANLINE_ORDER_UNSPECIFIED
        desc.BufferDesc.ScanlineOrdering = DXGI_MODE_SCANLINE_ORDER_UNSPECIFIED
        from ornata.api.exports.interop import DXGI_MODE_SCALING_UNSPECIFIED
        desc.BufferDesc.Scaling = DXGI_MODE_SCALING_UNSPECIFIED
        desc.SampleDesc.Count = 1
        desc.SampleDesc.Quality = 0
        from ornata.api.exports.interop import DXGI_USAGE_RENDER_TARGET_OUTPUT
        desc.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT
        desc.BufferCount = 2
        desc.OutputWindow = self._hwnd
        desc.Windowed = True
        from ornata.api.exports.interop import DXGI_SWAP_EFFECT_DISCARD
        desc.SwapEffect = DXGI_SWAP_EFFECT_DISCARD
        desc.Flags = 0

        hr, swap_chain_ptr = dxgi_factory.CreateSwapChain(self._device, desc)
        if hr != 0:
            raise RuntimeError(f"CreateSwapChain failed: hr={hr}")
        self._swap_chain = swap_chain_ptr
        self._initialized = True
        logger.debug("DirectX swap chain initialized successfully")

    def present(self) -> None:
        """Present the swap chain's back buffer to the screen."""
        if not self._initialized or self._swap_chain is None:
            raise RuntimeError("Swap chain is not initialized")
        self._swap_chain.Present(1, 0)

    def cleanup(self) -> None:
        """Mark this swap chain as uninitialized (COM wrapper manages lifetime)."""
        self._initialized = False