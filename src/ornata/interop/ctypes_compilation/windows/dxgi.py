"""DXGI structures, constants, and COM helpers used by the DirectX bindings."""

from __future__ import annotations

import ctypes as ct
import enum

from ornata.interop.ctypes_compilation.windows.com import COMInterface, COMPointer
from ornata.interop.ctypes_compilation.windows.foundation import (
    BOOL,
    GUID,
    HRESULT,
    UINT,
    WindowsLibraryError,
    check_hresult,
    ensure_windows,
    load_library,
)


class DXGI_FORMAT(enum.IntEnum):
    """Subset of DXGI formats required by Ornata."""

    UNKNOWN = 0
    R32G32B32A32_FLOAT = 2
    R32G32B32_FLOAT = 6
    R32G32_FLOAT = 16
    R8G8B8A8_UNORM = 28
    R32_UINT = 42
    R16_UINT = 57


DXGI_FORMAT_UNKNOWN = DXGI_FORMAT.UNKNOWN
DXGI_FORMAT_R32G32B32A32_FLOAT = DXGI_FORMAT.R32G32B32A32_FLOAT
DXGI_FORMAT_R32G32B32_FLOAT = DXGI_FORMAT.R32G32B32_FLOAT
DXGI_FORMAT_R32G32_FLOAT = DXGI_FORMAT.R32G32_FLOAT
DXGI_FORMAT_R8G8B8A8_UNORM = DXGI_FORMAT.R8G8B8A8_UNORM
DXGI_FORMAT_R32_UINT = DXGI_FORMAT.R32_UINT
DXGI_FORMAT_R16_UINT = DXGI_FORMAT.R16_UINT

DXGI_USAGE_SHADER_INPUT = 0x00000010
DXGI_USAGE_RENDER_TARGET_OUTPUT = 0x00000020

DXGI_SWAP_EFFECT_DISCARD = 0
DXGI_SWAP_EFFECT_SEQUENTIAL = 1
DXGI_SWAP_EFFECT_FLIP_SEQUENTIAL = 3
DXGI_SWAP_EFFECT_FLIP_DISCARD = 4

DXGI_MODE_SCANLINE_ORDER_UNSPECIFIED = 0
DXGI_MODE_SCALING_UNSPECIFIED = 0


class DXGI_RATIONAL(ct.Structure):
    """Numerator/denominator pair used by DXGI."""

    _fields_ = [("Numerator", UINT), ("Denominator", UINT)]


class DXGI_SAMPLE_DESC(ct.Structure):
    """Sample description for multisampling."""

    _fields_ = [("Count", UINT), ("Quality", UINT)]


class DXGI_MODE_DESC(ct.Structure):
    """Mode description for swap chain buffers."""

    _fields_ = [
        ("Width", UINT),
        ("Height", UINT),
        ("RefreshRate", DXGI_RATIONAL),
        ("Format", UINT),
        ("ScanlineOrdering", UINT),
        ("Scaling", UINT),
    ]


class DXGI_SWAP_CHAIN_DESC(ct.Structure):
    """Swap chain configuration for ``IDXGIFactory::CreateSwapChain``."""

    _fields_ = [
        ("BufferDesc", DXGI_MODE_DESC),
        ("SampleDesc", DXGI_SAMPLE_DESC),
        ("BufferUsage", UINT),
        ("BufferCount", UINT),
        ("OutputWindow", ct.c_void_p),
        ("Windowed", BOOL),
        ("SwapEffect", UINT),
        ("Flags", UINT),
    ]


IID_IDXGIFactory = GUID("{7B7166EC-21C7-44AE-B21A-C9AE321AE369}")
IID_IDXGISwapChain = GUID("{310D36A0-D2E7-4C0A-AA04-6A9D23B8886A}")


class IDXGISwapChain(COMInterface):
    """Subset of the ``IDXGISwapChain`` COM interface."""

    _methods_ = {
        "AddRef": (1, UINT, ()),
        "Release": (2, UINT, ()),
        "Present": (8, HRESULT, (UINT, UINT)),
        "GetBuffer": (9, HRESULT, (UINT, ct.POINTER(GUID), ct.POINTER(ct.c_void_p))),
        # Missing feature added:
        "ResizeBuffers": (13, HRESULT, (UINT, UINT, UINT, UINT, UINT)),
    }

    def Present(self, sync_interval: int, flags: int) -> int:
        return int(self._invoke("Present", UINT(sync_interval), UINT(flags)))

    def GetBuffer(self, buffer_index: int, iid: GUID) -> tuple[int, COMPointer]:
        buffer_ptr = COMPointer()
        hr = self._invoke("GetBuffer", UINT(buffer_index), ct.byref(iid), buffer_ptr.out_param())
        return int(hr), buffer_ptr

    def ResizeBuffers(self, buffer_count: int, width: int, height: int, new_format: int, flags: int) -> int:
        return int(self._invoke(
            "ResizeBuffers",
            UINT(buffer_count),
            UINT(width),
            UINT(height),
            UINT(new_format),
            UINT(flags),
        ))


class IDXGIFactory(COMInterface):
    """Subset of the ``IDXGIFactory`` COM interface."""

    _methods_ = {
        "CreateSwapChain": (10, HRESULT, (ct.c_void_p, ct.POINTER(DXGI_SWAP_CHAIN_DESC), ct.POINTER(ct.c_void_p))),
    }

    def CreateSwapChain(self, device: COMPointer | ct.c_void_p | int, desc: DXGI_SWAP_CHAIN_DESC) -> tuple[int, IDXGISwapChain]:
        swap_chain = IDXGISwapChain()
        hr = self._invoke("CreateSwapChain", _as_void_ptr(device), ct.byref(desc), swap_chain.out_param())
        return int(hr), swap_chain


def _as_void_ptr(value: COMPointer | ct.c_void_p | int | None) -> ct.c_void_p:
    if value is None:
        return ct.c_void_p()
    if isinstance(value, COMPointer):
        return value.pointer
    if isinstance(value, ct.c_void_p):
        return value
    return ct.c_void_p(int(value))


try:
    _dxgi = load_library("dxgi")
except WindowsLibraryError:
    _dxgi = None

_CreateDXGIFactory = None
if _dxgi is not None:
    _CreateDXGIFactory = ct.WINFUNCTYPE(HRESULT, ct.POINTER(GUID), ct.POINTER(ct.c_void_p))(("CreateDXGIFactory", _dxgi))


def CreateDXGIFactory() -> IDXGIFactory:
    """Create an ``IDXGIFactory`` instance."""
    ensure_windows()
    if _CreateDXGIFactory is None:
        raise WindowsLibraryError("dxgi.dll is not available")

    factory_ptr = ct.c_void_p()
    hr = _CreateDXGIFactory(ct.byref(IID_IDXGIFactory), ct.byref(factory_ptr))
    check_hresult(hr, "CreateDXGIFactory failed")

    factory = IDXGIFactory()
    factory.assign(factory_ptr)
    return factory


__all__ = [
    "CreateDXGIFactory",
    "DXGI_FORMAT",
    "DXGI_FORMAT_R32G32B32A32_FLOAT",
    "DXGI_FORMAT_R32G32B32_FLOAT",
    "DXGI_FORMAT_R32G32_FLOAT",
    "DXGI_FORMAT_R32_UINT",
    "DXGI_FORMAT_R16_UINT",
    "DXGI_FORMAT_R8G8B8A8_UNORM",
    "DXGI_MODE_DESC",
    "DXGI_MODE_SCALING_UNSPECIFIED",
    "DXGI_MODE_SCANLINE_ORDER_UNSPECIFIED",
    "DXGI_RATIONAL",
    "DXGI_SAMPLE_DESC",
    "DXGI_SWAP_CHAIN_DESC",
    "DXGI_SWAP_EFFECT_DISCARD",
    "DXGI_SWAP_EFFECT_FLIP_DISCARD",
    "DXGI_SWAP_EFFECT_FLIP_SEQUENTIAL",
    "DXGI_USAGE_RENDER_TARGET_OUTPUT",
    "DXGI_SWAP_EFFECT_SEQUENTIAL",
    "DXGI_USAGE_SHADER_INPUT",
    "IDXGIFactory",
    "IDXGISwapChain",
    "IID_IDXGIFactory",
    "IID_IDXGISwapChain",
]
