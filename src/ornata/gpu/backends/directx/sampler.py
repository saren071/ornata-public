# ===========================
# ornata/gpu/backends/directx/sampler.py
# ===========================
"""DirectX sampler state module.

Creates a linear-filter, clamp-address sampler suitable for UI rendering.
"""

from __future__ import annotations

import ctypes
from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.interop import ID3D11Device, ID3D11SamplerState

logger = get_logger(__name__)


class DirectXSampler:
    """Creates D3D11 sampler states."""

    def __init__(self, device: ID3D11Device | None) -> None:
        if device is None:
            raise ValueError("DirectXSampler requires a valid ID3D11Device")
        self._device = device
        self._initialized = True

    def create_sampler_state(self) -> ID3D11SamplerState:
        """Create a MIN_MAG_MIP_LINEAR + clamp sampler."""
        from ornata.api.exports.interop import (
            D3D11_COMPARISON_ALWAYS,
            D3D11_FILTER_MIN_MAG_MIP_LINEAR,
            D3D11_TEXTURE_ADDRESS_CLAMP,
        )

        if not self._initialized:
            raise RuntimeError("DirectXSampler not initialized")
        from ornata.api.exports.interop import D3D11_SAMPLER_DESC, ID3D11SamplerState
        desc = D3D11_SAMPLER_DESC()
        desc.Filter = D3D11_FILTER_MIN_MAG_MIP_LINEAR
        desc.AddressU = D3D11_TEXTURE_ADDRESS_CLAMP
        desc.AddressV = D3D11_TEXTURE_ADDRESS_CLAMP
        desc.AddressW = D3D11_TEXTURE_ADDRESS_CLAMP
        desc.MipLODBias = 0.0
        desc.MaxAnisotropy = 1
        desc.ComparisonFunc = D3D11_COMPARISON_ALWAYS
        border = (ctypes.c_float * 4)(0.0, 0.0, 0.0, 0.0)
        desc.BorderColor = border
        desc.MinLOD = 0.0
        desc.MaxLOD = 3.4028235e38  # FLT_MAX

        state_ptr = ID3D11SamplerState()
        hr = self._device.CreateSamplerState(desc, state_ptr)
        if int(hr) != 0:
            raise RuntimeError(f"CreateSamplerState failed: hr={hr}")
        return state_ptr