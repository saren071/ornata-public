# ornata/interop/ctypes_compilation/windows/ole32.py
"""ole32.dll bindings for COM initialization."""

from __future__ import annotations

import ctypes as ct

from ornata.interop.ctypes_compilation.windows.foundation import HRESULT, WindowsLibraryError, load_library

COINIT_MULTITHREADED = 0
COINIT_APARTMENTTHREADED = 2

try:
    _ole32 = load_library("ole32")
except WindowsLibraryError:
    _ole32 = None

CoInitializeEx = None
CoUninitialize = None
if _ole32 is not None:
    CoInitializeEx = _ole32.CoInitializeEx
    CoInitializeEx.argtypes = [ct.c_void_p, ct.c_uint]
    CoInitializeEx.restype = HRESULT

    CoUninitialize = _ole32.CoUninitialize
    CoUninitialize.argtypes = []
    CoUninitialize.restype = None


__all__ = ["COINIT_APARTMENTTHREADED", "COINIT_MULTITHREADED", "CoInitializeEx", "CoUninitialize"]
