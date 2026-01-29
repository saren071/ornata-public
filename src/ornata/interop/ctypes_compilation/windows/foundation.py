# ornata/interop/ctypes_compilation/windows/foundation.py
"""Core Windows ctypes helpers and common structures."""

from __future__ import annotations

import ctypes as ct
import ctypes.wintypes as ctwt
import sys
from collections.abc import Callable
from typing import Any

IS_WINDOWS = sys.platform == "win32"


class WindowsLibraryError(RuntimeError):
    """Raised when a required Windows library cannot be loaded."""


def ensure_windows() -> None:
    """Ensure the current interpreter is running on Windows."""
    if not IS_WINDOWS:
        raise WindowsLibraryError("Windows-specific bindings requested on a non-Windows platform")


LibraryLoader = Callable[[str], ct.WinDLL]


def load_library(name: str, loader: LibraryLoader | None = None) -> ct.WinDLL:
    """Load a Windows DLL with error handling."""
    ensure_windows()
    try:
        if loader is None:
            return ct.WinDLL(name, use_last_error=True)
        return loader(name)
    except OSError as exc:
        raise WindowsLibraryError(f"Failed to load '{name}.dll': {exc}") from exc


# Common Win32 typedefs --------------------------------------------------------------
HRESULT = ctwt.HRESULT
BOOL = ctwt.BOOL
UINT = ctwt.UINT
UINT32 = ctwt.UINT
UINT64 = ct.c_ulonglong
INT = ctwt.INT
DWORD = ctwt.DWORD
WORD = ctwt.WORD
BYTE = ctwt.BYTE
FLOAT = ct.c_float
DOUBLE = ct.c_double
SIZE_T = ct.c_size_t
LPVOID = ctwt.LPVOID
LPCWSTR = ctwt.LPCWSTR
LPCSTR = ctwt.LPCSTR
HANDLE = ctwt.HANDLE
HWND = ctwt.HWND
HINSTANCE = ctwt.HINSTANCE
HMODULE = ctwt.HMODULE


class RECT(ct.Structure):
    """Win32 RECT structure."""

    _fields_ = [("left", ct.c_long), ("top", ct.c_long), ("right", ct.c_long), ("bottom", ct.c_long)]


class POINT(ct.Structure):
    """Win32 POINT structure."""

    _fields_ = [("x", ct.c_long), ("y", ct.c_long)]


class COORD(ct.Structure):
    """Win32 COORD structure used by console APIs."""

    _fields_ = [("X", ct.c_short), ("Y", ct.c_short)]


class SMALL_RECT(ct.Structure):
    """Win32 SMALL_RECT structure used in console screen buffer info."""

    _fields_ = [
        ("Left", ct.c_short),
        ("Top", ct.c_short),
        ("Right", ct.c_short),
        ("Bottom", ct.c_short),
    ]


class SIZE(ct.Structure):
    """Win32 SIZE structure."""

    _fields_ = [("cx", ct.c_long), ("cy", ct.c_long)]


class PAINTSTRUCT(ct.Structure):
    """Win32 PAINTSTRUCT structure (defined explicitly to avoid platform/type ambiguity)."""

    _fields_ = [
        ("hdc", ct.c_void_p),
        ("fErase", BOOL),
        ("rcPaint", RECT),
        ("fRestore", BOOL),
        ("fIncUpdate", BOOL),
        ("rgbReserved", ct.c_byte * 32),
    ]


class GUID(ct.Structure):
    """GUID structure used across COM interfaces."""

    _fields_ = [
        ("Data1", DWORD),
        ("Data2", WORD),
        ("Data3", WORD),
        ("Data4", BYTE * 8),
    ]

    def __init__(self, spec: str | None = None) -> None:
        """Initialize a GUID from a canonical string when provided."""
        super().__init__()
        if spec:
            from uuid import UUID

            uid = UUID(spec)
            self.Data1 = uid.time_low
            self.Data2 = uid.time_mid
            self.Data3 = uid.time_hi_version
            data_tail = uid.bytes[8:]
            for index, value in enumerate(data_tail):
                self.Data4[index] = value


class LUID(ct.Structure):
    """Locally unique identifier."""

    _fields_ = [("LowPart", DWORD), ("HighPart", ct.c_long)]


def check_hresult(hr: int, message: str | None = None) -> None:
    """Validate an HRESULT and raise an exception on failure."""
    if hr < 0:
        detail = message or f"HRESULT 0x{hr & 0xFFFFFFFF:08X} indicates failure"
        raise WindowsLibraryError(detail)


def to_int(value: Any, restype: Any | None = None) -> int:
    """Robust conversion of a return value to int, handling unexpected byte strings."""
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)

    if isinstance(value, bytes):
        if len(value) == 4:
            import struct

            # Check restype name or identity to pick signed/unsigned
            is_unsigned = False
            if restype is not None:
                name = getattr(restype, "__name__", "").upper()
                if "UINT" in name or "DWORD" in name:
                    is_unsigned = True

            return struct.unpack("<I" if is_unsigned else "<i", value)[0]
        if len(value) == 8:
            import struct

            return struct.unpack("<Q" if restype and "UINT" in getattr(restype, "__name__", "").upper() else "<q", value)[0]

    try:
        # Check for COMPointer-like objects with a .pointer property
        if hasattr(value, "pointer"):
            try:
                # Recursively call to_int on the underlying pointer
                return to_int(value.pointer)
            except Exception:
                pass

        # Only attempt int() if it's a string, float, or other numeric-ish type
        if isinstance(value, (str, bytes)):
            return int(value)
        return int(value)
    except (TypeError, ValueError):
        # If it's something ctypes-like, try .value
        if hasattr(value, "value"):
            try:
                # Handle c_void_p(None) -> None.value is None
                v = value.value
                return int(v if v is not None else 0)
            except (TypeError, ValueError):
                pass
        # Try casting to void_p for pointer types
        try:
            return int(ct.cast(value, ct.c_void_p).value or 0)
        except Exception:
            pass
        return 0


__all__ = [
    "BOOL",
    "BYTE",
    "COORD",
    "DWORD",
    "DOUBLE",
    "FLOAT",
    "GUID",
    "HANDLE",
    "HINSTANCE",
    "HMODULE",
    "HWND",
    "INT",
    "IS_WINDOWS",
    "LPCSTR",
    "LPCWSTR",
    "LPVOID",
    "LUID",
    "PAINTSTRUCT",
    "POINT",
    "RECT",
    "SMALL_RECT",
    "SIZE",
    "SIZE_T",
    "UINT",
    "UINT32",
    "UINT64",
    "WORD",
    "to_int",
    "check_hresult",
    "ensure_windows",
    "load_library",
    "ctwt",
    "WindowsLibraryError",
]
