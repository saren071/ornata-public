# ===========================
# ornata/gpu/backends/directx/pipeline.py
# ===========================
"""DirectX pipeline state management module.

Creates basic Rasterizer, Depth-Stencil, and Blend states.
All functions raise on failure — no simulated fallbacks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.interop import ID3D11BlendState, ID3D11DepthStencilState, ID3D11Device, ID3D11RasterizerState

logger = get_logger(__name__)


class DirectXPipeline:
    """Manages D3D11 pipeline state objects."""

    def __init__(self, device: ID3D11Device) -> None:
        self._device = device
        self._initialized = True

    def create_rasterizer_state(self) -> ID3D11RasterizerState:
        """Create a standard solid-fill, back-face cull rasterizer state."""
        from ornata.api.exports.interop import D3D11_CULL_BACK, D3D11_FILL_SOLID

        if not self._initialized:
            raise RuntimeError("DirectXPipeline not initialized")

        from ornata.api.exports.interop import D3D11_RASTERIZER_DESC, ID3D11RasterizerState
        desc = D3D11_RASTERIZER_DESC()
        desc.FillMode = D3D11_FILL_SOLID
        desc.CullMode = D3D11_CULL_BACK
        desc.FrontCounterClockwise = False
        desc.DepthBias = 0
        desc.DepthBiasClamp = 0.0
        desc.SlopeScaledDepthBias = 0.0
        desc.DepthClipEnable = True
        desc.ScissorEnable = False
        desc.MultisampleEnable = False
        desc.AntialiasedLineEnable = False

        state_ptr = ID3D11RasterizerState()
        hr = self._device.CreateRasterizerState(desc, state_ptr)
        if int(hr) != 0:
            raise RuntimeError(f"CreateRasterizerState failed: hr={hr}")
        return state_ptr

    def create_depth_stencil_state(self) -> ID3D11DepthStencilState:
        """Create a depth-enabled, less-than compare depth stencil state."""
        from ornata.api.exports.interop import D3D11_COMPARISON_LESS, D3D11_DEPTH_WRITE_MASK_ALL

        if not self._initialized:
            raise RuntimeError("DirectXPipeline not initialized")

        from ornata.api.exports.interop import D3D11_DEPTH_STENCIL_DESC, ID3D11DepthStencilState
        desc = D3D11_DEPTH_STENCIL_DESC()
        desc.DepthEnable = True
        desc.DepthWriteMask = D3D11_DEPTH_WRITE_MASK_ALL
        desc.DepthFunc = D3D11_COMPARISON_LESS
        desc.StencilEnable = False
        desc.StencilReadMask = 0xFF
        desc.StencilWriteMask = 0xFF

        state_ptr = ID3D11DepthStencilState()
        hr = self._device.CreateDepthStencilState(desc, state_ptr)
        if int(hr) != 0:
            raise RuntimeError(f"CreateDepthStencilState failed: hr={hr}")
        return state_ptr

    def create_blend_state(self) -> ID3D11BlendState:
        """Create a disabled-blend state with full color mask."""
        from ornata.api.exports.interop import (
            D3D11_BLEND_DESC,
            D3D11_BLEND_ONE,
            D3D11_BLEND_OP_ADD,
            D3D11_BLEND_ZERO,
            D3D11_COLOR_WRITE_ENABLE_ALL,
        )

        if not self._initialized:
            raise RuntimeError("DirectXPipeline not initialized")

        desc = D3D11_BLEND_DESC()
        desc.AlphaToCoverageEnable = False
        desc.IndependentBlendEnable = False

        from ornata.api.exports.interop import D3D11_RENDER_TARGET_BLEND_DESC, ID3D11BlendState
        rt_desc = D3D11_RENDER_TARGET_BLEND_DESC()
        rt_desc.BlendEnable = False
        rt_desc.SrcBlend = D3D11_BLEND_ONE
        rt_desc.DestBlend = D3D11_BLEND_ZERO
        rt_desc.BlendOp = D3D11_BLEND_OP_ADD
        rt_desc.SrcBlendAlpha = D3D11_BLEND_ONE
        rt_desc.DestBlendAlpha = D3D11_BLEND_ZERO
        rt_desc.BlendOpAlpha = D3D11_BLEND_OP_ADD
        rt_desc.RenderTargetWriteMask = int(D3D11_COLOR_WRITE_ENABLE_ALL)

        desc.RenderTarget[0] = rt_desc

        state_ptr = ID3D11BlendState()
        hr = self._device.CreateBlendState(desc, state_ptr)
        if int(hr) != 0:
            raise RuntimeError(f"CreateBlendState failed: hr={hr}")
        return state_ptr