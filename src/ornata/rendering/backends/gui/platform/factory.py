"""Platform interface factory for GUI window management.

Provides a small abstraction that picks the appropriate window
manager for the current platform while falling back to a headless
implementation when native integrations are unavailable.
"""

from __future__ import annotations

import sys
from typing import Any

from ornata.api.exports.definitions import WindowManagerProtocol
from ornata.utils import get_logger

logger = get_logger(__name__)


class PlatformInterface:
    """Simple wrapper exposing a window manager."""

    def __init__(self, window_manager: WindowManagerProtocol) -> None:
        self._window_manager = window_manager

    def get_window_manager(self) -> WindowManagerProtocol:
        """Return the window manager instance."""

        return self._window_manager


class _HeadlessWindow:
    """In-memory placeholder window used when no native backend is available."""

    def __init__(self, title: str, width: int, height: int) -> None:
        self.title = title
        self.width = width
        self.height = height
        self._gpu_context: Any | None = None
        self._running = True

    def create_gpu_context(self, backend: str) -> None:
        """Create a dummy GPU context so the runtime continues to function."""

        logger.info("Headless window using CPU fallback for backend '%s'", backend)
        self._gpu_context = None

    def get_gpu_context(self) -> Any | None:
        """Return the stored GPU context (always ``None`` for headless)."""

        return self._gpu_context

    def resize(self, width: int, height: int) -> None:
        """Resize the headless window."""

        self.width = width
        self.height = height

    def close(self) -> None:
        """Mark the window as closed."""

        self._running = False


class _HeadlessWindowManager(WindowManagerProtocol):
    """Window manager that always returns headless windows."""

    def is_window_available(self) -> bool:
        return True

    def create_window(self, title: str, width: int, height: int) -> _HeadlessWindow:
        logger.info("Creating headless window '%s' (%dx%d)", title, width, height)
        return _HeadlessWindow(title, width, height)


def _build_win32_manager() -> WindowManagerProtocol | None:
    """Build a Win32 window manager if the bindings are available."""
    from ornata.api.exports.definitions import Win32WindowManager
    from ornata.rendering.backends.gui.platform.win32.window import Win32Window, is_available

    manager = Win32WindowManager(window_cls=Win32Window, availability=is_available)
    if not manager.is_window_available():
        return None
    return manager


def get_platform_interface() -> PlatformInterface:
    """Return the best available platform interface for GUI rendering."""

    if sys.platform.startswith("win"):
        win32_manager = _build_win32_manager()
        if win32_manager is not None:
            logger.debug("Using Win32 window manager")
            return PlatformInterface(win32_manager)
        logger.warning("Win32 window manager unavailable; falling back to headless implementation")

    logger.info("Using headless GUI window manager")
    return PlatformInterface(_HeadlessWindowManager())


__all__ = ["PlatformInterface", "get_platform_interface"]
