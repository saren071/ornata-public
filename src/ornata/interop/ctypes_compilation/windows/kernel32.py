# ornata/interop/ctypes_compilation/windows/kernel32.py
"""kernel32.dll bindings used across the project."""

from __future__ import annotations

import ctypes as ct

from ornata.interop.ctypes_compilation.windows.foundation import (
    BOOL,
    COORD,
    DWORD,
    HANDLE,
    HMODULE,
    LPCWSTR,
    SMALL_RECT,
    WindowsLibraryError,
    load_library,
)

try:
    _kernel32 = load_library("kernel32")
except WindowsLibraryError:
    _kernel32 = None

STD_INPUT_HANDLE = ct.c_ulong(-10 & 0xFFFFFFFF).value
STD_OUTPUT_HANDLE = ct.c_ulong(-11 & 0xFFFFFFFF).value
STD_ERROR_HANDLE = ct.c_ulong(-12 & 0xFFFFFFFF).value
INVALID_HANDLE_VALUE = ct.c_void_p(-1).value


class CONSOLE_SCREEN_BUFFER_INFO(ct.Structure):
    """Structure returned by ``GetConsoleScreenBufferInfo``."""

    _fields_ = [
        ("dwSize", COORD),
        ("dwCursorPosition", COORD),
        ("wAttributes", ct.c_ushort),
        ("srWindow", SMALL_RECT),
        ("dwMaximumWindowSize", COORD),
    ]


GetModuleHandleW = None
GetStdHandle = None
GetConsoleScreenBufferInfo = None
GetConsoleMode = None
SetConsoleMode = None
if _kernel32 is not None:
    GetModuleHandleW = _kernel32.GetModuleHandleW
    GetModuleHandleW.argtypes = [LPCWSTR]
    GetModuleHandleW.restype = HMODULE

    GetStdHandle = _kernel32.GetStdHandle
    GetStdHandle.argtypes = [ct.c_ulong]
    GetStdHandle.restype = HANDLE

    GetConsoleScreenBufferInfo = _kernel32.GetConsoleScreenBufferInfo
    GetConsoleScreenBufferInfo.argtypes = [HANDLE, ct.POINTER(CONSOLE_SCREEN_BUFFER_INFO)]
    GetConsoleScreenBufferInfo.restype = BOOL

    GetConsoleMode = _kernel32.GetConsoleMode
    GetConsoleMode.argtypes = [HANDLE, ct.POINTER(DWORD)]
    GetConsoleMode.restype = BOOL

    SetConsoleMode = _kernel32.SetConsoleMode
    SetConsoleMode.argtypes = [HANDLE, DWORD]
    SetConsoleMode.restype = BOOL


__all__ = [
    "CONSOLE_SCREEN_BUFFER_INFO",
    "GetConsoleScreenBufferInfo",
    "GetConsoleMode",
    "GetModuleHandleW",
    "GetStdHandle",
    "SetConsoleMode",
    "STD_ERROR_HANDLE",
    "STD_INPUT_HANDLE",
    "STD_OUTPUT_HANDLE",
    "INVALID_HANDLE_VALUE",
    "DWORD",
]


def get_console_mode(handle: int) -> int | None:
    """Return current console mode for ``handle`` or ``None`` on failure."""

    if GetConsoleMode is None:
        return None
    mode = DWORD()
    if not GetConsoleMode(handle, ct.byref(mode)):
        return None
    return mode.value


def set_console_mode(handle: int, mode_value: int) -> bool:
    """Set console mode for ``handle`` returning success flag."""

    if SetConsoleMode is None:
        return False
    return bool(SetConsoleMode(handle, DWORD(mode_value)))


__all__.extend(["get_console_mode", "set_console_mode"])
