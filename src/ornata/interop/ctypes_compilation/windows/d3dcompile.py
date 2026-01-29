"""Bindings for ``d3dcompiler_47.dll``."""

from __future__ import annotations

import ctypes as ct

from ornata.interop.ctypes_compilation.windows.foundation import (
    WindowsLibraryError,
    ensure_windows,
    load_library,
    to_int,
)

# ---------------------------------------------------------------------------
# Core COM Blob definition
# ---------------------------------------------------------------------------

class ID3DBlob(ct.Structure):
    """Opaque blob interface returned by ``D3DCompile``."""
    _fields_ = [("lpVtbl", ct.c_void_p)]


# ---------------------------------------------------------------------------
# Library load
# ---------------------------------------------------------------------------

try:
    _d3dcompiler = load_library("d3dcompiler_47")
except WindowsLibraryError:
    _d3dcompiler = None

_D3DCompile = None
if _d3dcompiler is not None:
    _D3DCompile = _d3dcompiler.D3DCompile
    _D3DCompile.argtypes = [
        ct.c_void_p,            # pSrcData
        ct.c_size_t,            # SrcDataSize
        ct.c_char_p,            # pSourceName
        ct.c_void_p,            # pDefines (D3D_SHADER_MACRO*)
        ct.c_void_p,            # pInclude (ID3DInclude*)
        ct.c_char_p,            # pEntrypoint
        ct.c_char_p,            # pTarget
        ct.c_uint,              # Flags1
        ct.c_uint,              # Flags2
        ct.POINTER(ct.c_void_p),# ppCode (ID3DBlob**)
        ct.POINTER(ct.c_void_p),# ppErrorMsgs (ID3DBlob**)
    ]
    _D3DCompile.restype = ct.c_long


# ---------------------------------------------------------------------------
# D3DCompile wrapper (safe for Python)
# ---------------------------------------------------------------------------

def D3DCompile(
    source: bytes,
    entry_point: bytes,
    target: bytes,
    flags1: int = 0,
    flags2: int = 0,
) -> tuple[int, ct.c_void_p, ct.c_void_p]:
    """Compile HLSL source code to bytecode.

    Args:
        source: UTF-8 encoded HLSL source
        entry_point: Entry point name (e.g., b"mainVS")
        target: Shader model (e.g., b"vs_5_0")
        flags1, flags2: Optional compile flags

    Returns:
        (HRESULT, code_blob_ptr, error_blob_ptr)
    """
    ensure_windows()
    if _D3DCompile is None:
        raise WindowsLibraryError("d3dcompiler_47.dll is not available")

    # Create a persistent memory buffer so the GC cannot move it
    src_buf = ct.create_string_buffer(source)
    src_ptr = ct.cast(src_buf, ct.c_void_p)
    src_size = len(source)

    pp_code = ct.c_void_p()
    pp_errors = ct.c_void_p()

    hr = _D3DCompile(
        src_ptr,                       # LPCVOID pSrcData
        ct.c_size_t(src_size),          # SIZE_T SrcDataSize
        None,                           # LPCSTR pSourceName
        None,                           # pDefines
        None,                           # pInclude
        entry_point,                    # LPCSTR pEntrypoint
        target,                         # LPCSTR pTarget
        ct.c_uint(flags1),              # Flags1
        ct.c_uint(flags2),              # Flags2
        ct.byref(pp_code),              # ppCode
        ct.byref(pp_errors),            # ppErrorMsgs
    )

    return to_int(hr, ct.c_long), pp_code, pp_errors


# ---------------------------------------------------------------------------
# Blob to bytes utility
# ---------------------------------------------------------------------------

def blob_to_bytes(blob_ptr: ct.c_void_p) -> bytes:
    """Convert an ID3DBlob pointer into a Python bytes object."""
    if not blob_ptr:
        return b""

    class _BlobVTable(ct.Structure):
        _fields_ = [("lpVtbl", ct.POINTER(ct.c_void_p))]

    blob_addr = int(blob_ptr.value or 0)
    if blob_addr == 0:
        return b""

    # ID3DBlob vtable indices:
    # [0]=QueryInterface, [1]=AddRef, [2]=Release,
    # [3]=GetBufferPointer, [4]=GetBufferSize
    vtbl = ct.cast(_BlobVTable.from_address(blob_addr).lpVtbl,
                   ct.POINTER(ct.c_void_p * 5))

    GetBufferPointer = ct.WINFUNCTYPE(ct.c_void_p, ct.c_void_p)(vtbl.contents[3])
    GetBufferSize = ct.WINFUNCTYPE(ct.c_size_t, ct.c_void_p)(vtbl.contents[4])

    ptr = GetBufferPointer(blob_ptr)
    size = GetBufferSize(blob_ptr)
    if not ptr or size == 0:
        return b""

    return ct.string_at(ptr, size)


__all__ = ["D3DCompile", "ID3DBlob", "blob_to_bytes"]
