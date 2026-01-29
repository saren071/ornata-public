# ornata/interop/ctypes_compilation/registry.py
"""Platform-specific ctypes bindings for Ornata.

This package centralizes all low-level operating-system and graphics API
interactions that rely on ``ctypes``.  Callers should use
``get_platform_bindings`` to obtain the modules appropriate to the host
platform rather than importing deep subpackages directly.  That keeps the
call-sites clean while still allowing each platform to expose the full set of
structures, constants, and helpers that Ornata relies on.
"""

from __future__ import annotations

import importlib
import sys
from typing import Any

from ornata.api.exports.definitions import BindingGroup

_BINDING_TABLE: dict[str, BindingGroup] = {
    "win32": BindingGroup(
        foundation="ornata.interop.ctypes_compilation.windows.foundation",
        com="ornata.interop.ctypes_compilation.windows.com",
        graphics={
            "dxgi": "ornata.interop.ctypes_compilation.windows.dxgi",
            "d3d11": "ornata.interop.ctypes_compilation.windows.d3d11",
            "d3dcompile": "ornata.interop.ctypes_compilation.windows.d3dcompile",
            "opengl": "ornata.interop.ctypes_compilation.windows.opengl",
        },
        windowing={
            "user32": "ornata.interop.ctypes_compilation.windows.user32",
            "gdi32": "ornata.interop.ctypes_compilation.windows.gdi32",
            "kernel32": "ornata.interop.ctypes_compilation.windows.kernel32",
            "ole32": "ornata.interop.ctypes_compilation.windows.ole32",
        },
    ),
    # Additional platforms can be registered here as they gain ctypes coverage.
}


def get_platform_bindings(platform: str | None = None) -> dict[str, Any]:
    """Load platform-specific binding modules."""
    platform_key = platform or sys.platform
    group = _BINDING_TABLE.get(platform_key)
    if group is None:
        raise ImportError(f"No ctypes bindings registered for platform '{platform_key}'")

    resolved: dict[str, Any] = {}
    resolved["foundation"] = importlib.import_module(group.foundation)
    if group.com:
        resolved["com"] = importlib.import_module(group.com)

    resolved["graphics"] = {
        name: importlib.import_module(path) for name, path in group.graphics.items()
    }
    resolved["windowing"] = {
        name: importlib.import_module(path) for name, path in group.windowing.items()
    }
    return resolved


__all__ = ["BindingGroup", "get_platform_bindings"]
