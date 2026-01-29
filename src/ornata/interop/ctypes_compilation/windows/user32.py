# ornata/interop/ctypes_compilation/windows/user32.py
"""user32.dll bindings used by the GUI renderer."""

from __future__ import annotations

import ctypes as ct
from typing import Any, Protocol

from ornata.interop.ctypes_compilation.windows.foundation import (
    BOOL,
    HANDLE,
    HINSTANCE,
    HWND,
    INT,
    LPCWSTR,
    PAINTSTRUCT,
    UINT,
    WindowsLibraryError,
    ctwt,
    load_library,
)

LRESULT = ct.c_long
WPARAM = ct.c_size_t
LPARAM = ct.c_size_t

CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001

WM_DESTROY = 0x0002
WM_SIZE = 0x0005
WM_PAINT = 0x000F
WM_ERASEBKGND = 0x0014
WM_KEYDOWN = 0x0100
WM_LBUTTONDOWN = 0x0201

SW_SHOW = 5

WNDPROC = ct.WINFUNCTYPE(LRESULT, HWND, UINT, WPARAM, LPARAM)


class CFunctionPointer(Protocol):
    argtypes: list[Any]
    restype: Any

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


try:
    _user32 = load_library("user32")
except WindowsLibraryError:
    _user32 = None


class WNDCLASS(ct.Structure):
    """Window class definition used by ``RegisterClassW``."""

    _fields_ = [
        ("style", UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", INT),
        ("cbWndExtra", INT),
        ("hInstance", HINSTANCE),
        ("hIcon", HANDLE),
        ("hCursor", HANDLE),
        ("hbrBackground", HANDLE),
        ("lpszMenuName", LPCWSTR),
        ("lpszClassName", LPCWSTR),
    ]


def _proc(name: str) -> CFunctionPointer | None:
    if _user32 is None:
        return None
    return getattr(_user32, name)


RegisterClassW: CFunctionPointer | None = _proc("RegisterClassW")
if RegisterClassW is not None:
    RegisterClassW.argtypes = [ct.POINTER(WNDCLASS)]
    RegisterClassW.restype = ctwt.ATOM

CreateWindowExW: CFunctionPointer | None = _proc("CreateWindowExW")
if CreateWindowExW is not None:
    CreateWindowExW.argtypes = [
        ctwt.DWORD,     # dwExStyle
        LPCWSTR,        # lpClassName
        LPCWSTR,        # lpWindowName
        ctwt.DWORD,     # dwStyle
        ct.c_int,       # X
        ct.c_int,       # Y
        ct.c_int,       # nWidth
        ct.c_int,       # nHeight
        HWND,           # hWndParent
        ct.c_void_p,    # hMenu
        HINSTANCE,      # hInstance
        ct.c_void_p,    # lpParam
    ]
    CreateWindowExW.restype = HWND

ShowWindow: CFunctionPointer | None = _proc("ShowWindow")
if ShowWindow is not None:
    ShowWindow.argtypes = [HWND, INT]
    ShowWindow.restype = BOOL

UpdateWindow: CFunctionPointer | None = _proc("UpdateWindow")
if UpdateWindow is not None:
    UpdateWindow.argtypes = [HWND]
    UpdateWindow.restype = BOOL

DefWindowProcW: CFunctionPointer | None = _proc("DefWindowProcW")
if DefWindowProcW is not None:
    DefWindowProcW.argtypes = [HWND, UINT, WPARAM, LPARAM]
    DefWindowProcW.restype = LRESULT

DestroyWindow: CFunctionPointer | None = _proc("DestroyWindow")
if DestroyWindow is not None:
    DestroyWindow.argtypes = [HWND]
    DestroyWindow.restype = BOOL

TranslateMessage: CFunctionPointer | None = _proc("TranslateMessage")
if TranslateMessage is not None:
    TranslateMessage.argtypes = [ct.POINTER(ctwt.MSG)]
    TranslateMessage.restype = BOOL

DispatchMessageW: CFunctionPointer | None = _proc("DispatchMessageW")
if DispatchMessageW is not None:
    DispatchMessageW.argtypes = [ct.POINTER(ctwt.MSG)]
    DispatchMessageW.restype = LRESULT

PeekMessageW: CFunctionPointer | None = _proc("PeekMessageW")
if PeekMessageW is not None:
    PeekMessageW.argtypes = [ct.POINTER(ctwt.MSG), HWND, UINT, UINT, UINT]
    PeekMessageW.restype = BOOL

BeginPaint: CFunctionPointer | None = _proc("BeginPaint")
if BeginPaint is not None:
    BeginPaint.argtypes = [HWND, ct.POINTER(PAINTSTRUCT)]
    BeginPaint.restype = ctwt.HDC

EndPaint: CFunctionPointer | None = _proc("EndPaint")
if EndPaint is not None:
    EndPaint.argtypes = [HWND, ct.POINTER(PAINTSTRUCT)]
    EndPaint.restype = BOOL

InvalidateRect: CFunctionPointer | None = _proc("InvalidateRect")
if InvalidateRect is not None:
    InvalidateRect.argtypes = [HWND, ct.POINTER(ctwt.RECT), BOOL]
    InvalidateRect.restype = BOOL

PostQuitMessage: CFunctionPointer | None = _proc("PostQuitMessage")
if PostQuitMessage is not None:
    PostQuitMessage.argtypes = [INT]
    PostQuitMessage.restype = None

PostMessageW: CFunctionPointer | None = _proc("PostMessageW")
if PostMessageW is not None:
    PostMessageW.argtypes = [HWND, UINT, WPARAM, LPARAM]
    PostMessageW.restype = BOOL

SetWindowTextW: CFunctionPointer | None = _proc("SetWindowTextW")
if SetWindowTextW is not None:
    SetWindowTextW.argtypes = [HWND, LPCWSTR]
    SetWindowTextW.restype = BOOL

SetWindowPos: CFunctionPointer | None = _proc("SetWindowPos")
if SetWindowPos is not None:
    SetWindowPos.argtypes = [HWND, HWND, INT, INT, INT, INT, UINT]
    SetWindowPos.restype = BOOL

LoadCursorW: CFunctionPointer | None = _proc("LoadCursorW")
if LoadCursorW is not None:
    LoadCursorW.argtypes = [HINSTANCE, LPCWSTR]
    LoadCursorW.restype = ctwt.HCURSOR

GetMessageW: CFunctionPointer | None = _proc("GetMessageW")
if GetMessageW is not None:
    GetMessageW.argtypes = [ct.POINTER(ctwt.MSG), HWND, UINT, UINT]
    GetMessageW.restype = INT

GetClientRect: CFunctionPointer | None = _proc("GetClientRect")
if GetClientRect is not None:
    GetClientRect.argtypes = [HWND, ct.POINTER(ctwt.RECT)]
    GetClientRect.restype = BOOL

FillRect: CFunctionPointer | None = _proc("FillRect")
if FillRect is not None:
    FillRect.argtypes = [ctwt.HDC, ct.POINTER(ctwt.RECT), HANDLE]
    FillRect.restype = INT

GetAsyncKeyState: CFunctionPointer | None = _proc("GetAsyncKeyState")
if GetAsyncKeyState is not None:
    GetAsyncKeyState.argtypes = [INT]
    GetAsyncKeyState.restype = ctwt.SHORT

GetDC: CFunctionPointer | None = _proc("GetDC")
if GetDC is not None:
    GetDC.argtypes = [HWND]
    GetDC.restype = ctwt.HDC

ReleaseDC: CFunctionPointer | None = _proc("ReleaseDC")
if ReleaseDC is not None:
    ReleaseDC.argtypes = [HWND, ctwt.HDC]
    ReleaseDC.restype = INT


__all__ = [
    "BeginPaint",
    "CS_HREDRAW",
    "CS_VREDRAW",
    "CreateWindowExW",
    "DefWindowProcW",
    "DestroyWindow",
    "DispatchMessageW",
    "EndPaint",
    "FillRect",
    "GetAsyncKeyState",
    "GetClientRect",
    "GetDC",
    "GetMessageW",
    "InvalidateRect",
    "LRESULT",
    "LoadCursorW",
    "PostMessageW",
    "PeekMessageW",
    "PostQuitMessage",
    "RegisterClassW",
    "ReleaseDC",
    "ShowWindow",
    "SW_SHOW",
    "TranslateMessage",
    "UpdateWindow",
    "SetWindowPos",
    "SetWindowTextW",
    "WM_DESTROY",
    "WM_ERASEBKGND",
    "WM_KEYDOWN",
    "WM_LBUTTONDOWN",
    "WM_PAINT",
    "WM_SIZE",
    "WNDCLASS",
    "WNDPROC",
    "WPARAM",
    "ctwt",
]
