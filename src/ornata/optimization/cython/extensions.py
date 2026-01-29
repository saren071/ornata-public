"""Cython optimization modules for Ornata."""

from __future__ import annotations

from importlib import import_module

from ornata.api.exports.definitions import CythonCompilationError
from ornata.api.exports.optimization import compile_cython_extensions


def _load_extension(module_name: str) -> object | None:
    """Return an optional Cython extension module when available.

    This function attempts to load Cython-compiled extensions. If the extension
    is not available (due to compilation failure or missing Cython), it returns
    None and logs the failure for debugging purposes.

    Args:
        module_name: The name of the Cython extension module to load.

    Returns:
        The loaded module if available, None otherwise.
    """
    try:
        module = import_module(module_name)
        # Test that the module loaded correctly by checking for expected attributes
        if hasattr(module, '__file__') and module.__file__:
            # Successfully loaded a compiled extension
            return module
        else:
            # Module loaded but may not be the compiled version
            return module
    except ImportError as e:
        # Cython extension not available - this is expected in some environments
        # Log at debug level since this is normal behavior
        from ornata.api.exports.utils import get_logger
        logger = get_logger(__name__)
        logger.debug(f"Cython extension '{module_name}' not available: {e}")
        return None
    except Exception as e:
        # Unexpected error during import
        from ornata.api.exports.utils import get_logger
        logger = get_logger(__name__)
        logger.warning(f"Unexpected error loading Cython extension '{module_name}': {e}")
        return None


style_ops = _load_extension("ornata.optimization.cython.style_ops")
color_ops = _load_extension("ornata.optimization.cython.color_ops")
event_queue = _load_extension("ornata.optimization.cython.event_queue")
event_coalescing = _load_extension("ornata.optimization.cython.event_coalescing")
event_dispatch = _load_extension("ornata.optimization.cython.event_dispatch")
event_structs = _load_extension("ornata.optimization.cython.event_structs")
event_optimizer = _load_extension("ornata.optimization.cython.event_optimizer")
vdom_diff = _load_extension("ornata.optimization.cython.vdom_diff")


def is_native_extension(module: object | None) -> bool:
    """Check if a loaded module is a native (compiled) Cython extension.

    Args:
        module: The module to check.

    Returns:
        True if the module is a compiled Cython extension, False if it's a fallback.
    """
    if module is None:
        return False

    # Check for Cython-specific attributes that indicate compiled extension
    if hasattr(module, '__file__') and module.__file__:
        # Check if it's a .so/.pyd file (compiled extension)
        import os.path
        _, ext = os.path.splitext(module.__file__)
        if ext in ('.so', '.pyd', '.dll'):
            return True

    # Check for Cython metadata
    if hasattr(module, '__cython_version__'):
        return True

    return False


def get_extension_status() -> dict[str, dict[str, bool]]:
    """Get the status of all Cython extensions (native vs fallback).

    Returns:
        Dictionary mapping extension names to their status info.
        Each status dict contains 'available' and 'native' boolean flags.
    """
    extensions = {
        "style_ops": style_ops,
        "color_ops": color_ops,
        "event_queue": event_queue,
        "event_coalescing": event_coalescing,
        "event_dispatch": event_dispatch,
        "event_structs": event_structs,
        "event_optimizer": event_optimizer,
    }

    status: dict[str, dict[str, bool]] = {}
    for name, module in extensions.items():
        status[name] = {
            "available": module is not None,
            "native": is_native_extension(module),
        }

    return status


def log_extension_status() -> None:
    """Log the current status of all Cython extensions for debugging."""
    from ornata.api.exports.utils import get_logger
    logger = get_logger(__name__)

    status = get_extension_status()

    logger.debug("Cython extension status:")
    for name, info in status.items():
        if info["available"]:
            ext_type = "native" if info["native"] else "fallback"
            logger.debug(f"  {name}: available ({ext_type})")
        else:
            logger.debug(f"  {name}: not available")


__all__ = [
    "compile_cython_extensions",
    "CythonCompilationError",
    "style_ops",
    "color_ops",
    "event_queue",
    "event_coalescing",
    "event_dispatch",
    "event_structs",
    "event_optimizer",
    "vdom_diff",
    "is_native_extension",
    "get_extension_status",
    "log_extension_status",
]
