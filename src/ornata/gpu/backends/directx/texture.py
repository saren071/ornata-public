# ===========================
# ornata/gpu/backends/directx/texture.py
# ===========================
"""DirectX texture operations module.

Provides creation of 2D textures and associated shader resource views (SRV).
All paths are fully implemented and raise on failure.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.interop import DXGI_FORMAT, ID3D11Device, ID3D11ShaderResourceView, ID3D11Texture2D

logger = get_logger(__name__)


class DirectXTexture:
    """Manages texture creation and SRV generation."""

    def __init__(self, device: ID3D11Device | None) -> None:
        if device is None:
            raise ValueError("DirectXTexture requires a valid ID3D11Device")
        self._device = device
        self._initialized = True

    def create_texture_2d(self, width: int, height: int, format: DXGI_FORMAT | None = None) -> ID3D11Texture2D:
        """Create a 2D texture with SHADER_RESOURCE binding."""
        if not self._initialized:
            raise RuntimeError("DirectXTexture not initialized")
        if width <= 0 or height <= 0:
            raise ValueError("Texture width/height must be positive")

        from ornata.api.exports.interop import D3D11_BIND_SHADER_RESOURCE, D3D11_TEXTURE2D_DESC, D3D11_USAGE_DEFAULT, DXGI_FORMAT_R8G8B8A8_UNORM, DXGI_SAMPLE_DESC, ID3D11Texture2D

        desc = D3D11_TEXTURE2D_DESC()
        desc.Width = int(width)
        desc.Height = int(height)
        desc.MipLevels = 1
        desc.ArraySize = 1
        desc.Format = format if format is not None else DXGI_FORMAT_R8G8B8A8_UNORM
        desc.SampleDesc = DXGI_SAMPLE_DESC(Count=1, Quality=0)
        desc.Usage = D3D11_USAGE_DEFAULT
        desc.BindFlags = D3D11_BIND_SHADER_RESOURCE
        desc.CPUAccessFlags = 0
        desc.MiscFlags = 0

        texture_ptr = ID3D11Texture2D()
        hr = self._device.CreateTexture2D(desc, None, texture_ptr)
        if int(hr) != 0:
            raise RuntimeError(f"CreateTexture2D failed: hr={hr}")
        return texture_ptr

    def create_shader_resource_view(self, texture: ID3D11Texture2D) -> ID3D11ShaderResourceView:
        """Create a Shader Resource View (SRV) for a 2D texture."""
        from ornata.api.exports.interop import D3D11_SHADER_RESOURCE_VIEW_DESC, D3D11_SRV_DIMENSION_TEXTURE2D, D3D11_TEX2D_SRV, DXGI_FORMAT_R8G8B8A8_UNORM, ID3D11ShaderResourceView, ID3D11Texture2D
        if not self._initialized:
            raise RuntimeError("DirectXTexture not initialized")
        if not isinstance(texture, ID3D11Texture2D):
            raise TypeError("texture must be an ID3D11Texture2D")

        desc = D3D11_SHADER_RESOURCE_VIEW_DESC()
        desc.Format = DXGI_FORMAT_R8G8B8A8_UNORM
        desc.ViewDimension = D3D11_SRV_DIMENSION_TEXTURE2D
        desc.Anonymous.Texture2D = D3D11_TEX2D_SRV(MostDetailedMip=0, MipLevels=1)

        srv_ptr = ID3D11ShaderResourceView()
        hr = self._device.CreateShaderResourceView(texture, desc, srv_ptr)
        if int(hr) != 0:
            raise RuntimeError(f"CreateShaderResourceView failed: hr={hr}")
        return srv_ptr