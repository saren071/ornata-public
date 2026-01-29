# ornata/interop/ctypes_compilation/windows/gdi32.py
"""gdi32.dll bindings supporting the Win32 renderer."""

from __future__ import annotations

import ctypes as ct
from typing import Any, Protocol

from ornata.interop.ctypes_compilation.windows.foundation import (
    BOOL,
    HANDLE,
    INT,
    UINT,
    WindowsLibraryError,
    ctwt,
    load_library,
)

TRANSPARENT = 1


class PIXELFORMATDESCRIPTOR(ct.Structure):
    """Windows PIXELFORMATDESCRIPTOR structure for pixel format selection."""
    _fields_ = [
        ("nSize", ct.c_ushort),
        ("nVersion", ct.c_ushort),
        ("dwFlags", ct.c_uint),
        ("iPixelType", ct.c_ubyte),
        ("cColorBits", ct.c_ubyte),
        ("cRedBits", ct.c_ubyte),
        ("cRedShift", ct.c_ubyte),
        ("cGreenBits", ct.c_ubyte),
        ("cGreenShift", ct.c_ubyte),
        ("cBlueBits", ct.c_ubyte),
        ("cBlueShift", ct.c_ubyte),
        ("cAlphaBits", ct.c_ubyte),
        ("cAlphaShift", ct.c_ubyte),
        ("cAccumBits", ct.c_ubyte),
        ("cAccumRedBits", ct.c_ubyte),
        ("cAccumGreenBits", ct.c_ubyte),
        ("cAccumBlueBits", ct.c_ubyte),
        ("cAccumAlphaBits", ct.c_ubyte),
        ("cDepthBits", ct.c_ubyte),
        ("cStencilBits", ct.c_ubyte),
        ("cAuxBuffers", ct.c_ubyte),
        ("iLayerType", ct.c_ubyte),
        ("bReserved", ct.c_ubyte),
        ("dwLayerMask", ct.c_uint),
        ("dwVisibleMask", ct.c_uint),
        ("dwDamageMask", ct.c_uint),
    ]


try:
    _gdi32 = load_library("gdi32")
except WindowsLibraryError:
    _gdi32 = None


class CFunctionPointer(Protocol):
    argtypes: list[Any]
    restype: Any

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


def _proc(name: str) -> CFunctionPointer | None:
    if _gdi32 is None:
        return None
    return getattr(_gdi32, name)


GetStockObject: CFunctionPointer | None = _proc("GetStockObject")
if GetStockObject is not None:
    GetStockObject.argtypes = [INT]
    GetStockObject.restype = HANDLE

CreateFontW: CFunctionPointer | None = _proc("CreateFontW")
if CreateFontW is not None:
    CreateFontW.argtypes = [
        INT,
        INT,
        INT,
        INT,
        INT,
        BOOL,
        BOOL,
        BOOL,
        UINT,
        UINT,
        UINT,
        UINT,
        UINT,
        ctwt.LPCWSTR,
    ]
    CreateFontW.restype = ctwt.HFONT

SelectObject: CFunctionPointer | None = _proc("SelectObject")
if SelectObject is not None:
    SelectObject.argtypes = [ctwt.HDC, HANDLE]
    SelectObject.restype = HANDLE

DeleteObject: CFunctionPointer | None = _proc("DeleteObject")
if DeleteObject is not None:
    DeleteObject.argtypes = [HANDLE]
    DeleteObject.restype = BOOL

SetTextColor: CFunctionPointer | None = _proc("SetTextColor")
if SetTextColor is not None:
    SetTextColor.argtypes = [ctwt.HDC, ctwt.COLORREF]
    SetTextColor.restype = ctwt.COLORREF

TextOutW: CFunctionPointer | None = _proc("TextOutW")
if TextOutW is not None:
    TextOutW.argtypes = [ctwt.HDC, INT, INT, ctwt.LPCWSTR, INT]
    TextOutW.restype = BOOL

SetBkMode: CFunctionPointer | None = _proc("SetBkMode")
if SetBkMode is not None:
    SetBkMode.argtypes = [ctwt.HDC, INT]
    SetBkMode.restype = INT

MoveToEx: CFunctionPointer | None = _proc("MoveToEx")
if MoveToEx is not None:
    MoveToEx.argtypes = [ctwt.HDC, INT, INT, ct.c_void_p]
    MoveToEx.restype = BOOL

LineTo: CFunctionPointer | None = _proc("LineTo")
if LineTo is not None:
    LineTo.argtypes = [ctwt.HDC, INT, INT]
    LineTo.restype = BOOL

CreateSolidBrush: CFunctionPointer | None = _proc("CreateSolidBrush")
if CreateSolidBrush is not None:
    CreateSolidBrush.argtypes = [ctwt.COLORREF]
    CreateSolidBrush.restype = ctwt.HBRUSH

CreatePen: CFunctionPointer | None = _proc("CreatePen")
if CreatePen is not None:
    CreatePen.argtypes = [INT, INT, ctwt.COLORREF]
    CreatePen.restype = ctwt.HPEN

GetTextExtentPoint32W: CFunctionPointer | None = _proc("GetTextExtentPoint32W")
if GetTextExtentPoint32W is not None:
    GetTextExtentPoint32W.argtypes = [ctwt.HDC, ctwt.LPCWSTR, INT, ct.POINTER(ctwt.SIZE)]
    GetTextExtentPoint32W.restype = BOOL

ChoosePixelFormat: CFunctionPointer | None = _proc("ChoosePixelFormat")
if ChoosePixelFormat is not None:
    ChoosePixelFormat.argtypes = [ctwt.HDC, ct.POINTER(PIXELFORMATDESCRIPTOR)]
    ChoosePixelFormat.restype = INT

SetPixelFormat: CFunctionPointer | None = _proc("SetPixelFormat")
if SetPixelFormat is not None:
    SetPixelFormat.argtypes = [ctwt.HDC, INT, ct.POINTER(PIXELFORMATDESCRIPTOR)]
    SetPixelFormat.restype = INT

SwapBuffers: CFunctionPointer | None = _proc("SwapBuffers")
if SwapBuffers is not None:
    SwapBuffers.argtypes = [ctwt.HDC]
    SwapBuffers.restype = INT


__all__ = [
    "ChoosePixelFormat",
    "CreateFontW",
    "CreatePen",
    "CreateSolidBrush",
    "DeleteObject",
    "GetStockObject",
    "GetTextExtentPoint32W",
    "LineTo",
    "MoveToEx",
    "PIXELFORMATDESCRIPTOR",
    "SelectObject",
    "SetBkMode",
    "SetPixelFormat",
    "SetTextColor",
    "SwapBuffers",
    "TextOutW",
    "TRANSPARENT",
    "ctwt",
]
