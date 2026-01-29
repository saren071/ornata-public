# ornata/interop/ctypes_compilation/windows/d3d11_devicecontext1.py
"""Direct3D 11.1 Device Context 1 interface (ID3D11DeviceContext1).

Provides extended methods for shader constant buffer binding with offsets,
introduced in Direct3D 11.1, including:
    - VSSetConstantBuffers1
    - PSSetConstantBuffers1

This interface extends ID3D11DeviceContext and uses compatible COM invocation.
"""

from __future__ import annotations

import ctypes as ct
from collections.abc import Sequence

from ornata.interop.ctypes_compilation.windows.d3d11 import ID3D11Buffer, ID3D11DeviceContext, _ptr_val  # type: ignore [private]
from ornata.interop.ctypes_compilation.windows.foundation import UINT


class ID3D11DeviceContext1(ID3D11DeviceContext):
    """Direct3D 11.1 device context extension.

    Adds support for per-constant-buffer offset ranges through
    VSSetConstantBuffers1 and PSSetConstantBuffers1, as defined in the
    Direct3D 11.1 API.
    """

    _methods_ = {
        **ID3D11DeviceContext._methods_,
        "VSSetConstantBuffers1": (
            150,  # vtable index in D3D11.1 ID3D11DeviceContext1
            None,
            (UINT, UINT, ct.POINTER(ct.c_void_p), ct.POINTER(UINT), ct.POINTER(UINT)),
        ),
        "PSSetConstantBuffers1": (
            151,
            None,
            (UINT, UINT, ct.POINTER(ct.c_void_p), ct.POINTER(UINT), ct.POINTER(UINT)),
        ),
    }

    def VSSetConstantBuffers1(
        self,
        start_slot: int,
        buffers: Sequence[ID3D11Buffer],
        first_constants: Sequence[int] | None = None,
        num_constants: Sequence[int] | None = None,
    ) -> None:
        """Bind constant buffers to the vertex shader with per-buffer offsets.

        Args:
            start_slot: The starting slot index.
            buffers: A sequence of ID3D11Buffer objects.
            first_constants: Optional list of starting constant indices.
            num_constants: Optional list of number of constants for each buffer.
        """
        count = len(buffers)
        buf_arr = (ct.c_void_p * count)(*[ct.c_void_p(_ptr_val(b)) for b in buffers])
        first_arr = (UINT * count)(*[UINT(fc) for fc in (first_constants or [0] * count)])
        num_arr = (UINT * count)(*[UINT(nc) for nc in (num_constants or [0] * count)])
        self._invoke(
            "VSSetConstantBuffers1",
            UINT(int(start_slot)),
            UINT(count),
            buf_arr,
            first_arr,
            num_arr,
        )

    def PSSetConstantBuffers1(
        self,
        start_slot: int,
        buffers: Sequence[ID3D11Buffer],
        first_constants: Sequence[int] | None = None,
        num_constants: Sequence[int] | None = None,
    ) -> None:
        """Bind constant buffers to the pixel shader with per-buffer offsets.

        Args:
            start_slot: The starting slot index.
            buffers: A sequence of ID3D11Buffer objects.
            first_constants: Optional list of starting constant indices.
            num_constants: Optional list of number of constants for each buffer.
        """
        count = len(buffers)
        buf_arr = (ct.c_void_p * count)(*[ct.c_void_p(_ptr_val(b)) for b in buffers])
        first_arr = (UINT * count)(*[UINT(fc) for fc in (first_constants or [0] * count)])
        num_arr = (UINT * count)(*[UINT(nc) for nc in (num_constants or [0] * count)])
        self._invoke(
            "PSSetConstantBuffers1",
            UINT(int(start_slot)),
            UINT(count),
            buf_arr,
            first_arr,
            num_arr,
        )

# Convenience wrappers for PSSetConstantBuffers1 and VSSetConstantBuffers1
PSSetConstantBuffers1 = ID3D11DeviceContext1.PSSetConstantBuffers1
VSSetConstantBuffers1 = ID3D11DeviceContext1.VSSetConstantBuffers1

__all__ = ["ID3D11DeviceContext1", "PSSetConstantBuffers1", "VSSetConstantBuffers1"]
