"""Terminal capability adapter for Windows Console Host.

This module provides detection and handling for Windows Console Host
terminal capabilities, including ANSI support detection and workarounds.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from ornata.api.exports.definitions import TerminalCapability, TerminalInfo, TerminalType
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.interop.ctypes_compilation.windows.kernel32 import CONSOLE_SCREEN_BUFFER_INFO as CsbiStruct

logger = get_logger(__name__)


class ConHostAdapter:
    """Adapter for Windows Console Host terminal capabilities."""

    def __init__(self) -> None:
        """Initialize the ConHost adapter."""
        self._detected_capabilities: set[TerminalCapability] | None = None
        self._terminal_info: TerminalInfo | None = None

    def detect_capabilities(self) -> TerminalInfo:
        """Detect Windows Console Host capabilities.

        Returns:
            TerminalInfo object with detected capabilities.
        """
        if self._terminal_info is not None:
            return self._terminal_info

        capabilities: set[TerminalCapability] = set()
        width, height = self._get_terminal_size()

        # Windows Console Host (conhost.exe) basic capabilities
        capabilities.add(TerminalCapability.ANSI_COLORS)
        capabilities.add(TerminalCapability.ANSI_CURSOR)

        # Check for ANSI screen buffer support (Windows 10 1511+)
        if self._supports_ansi_screen():
            capabilities.add(TerminalCapability.ANSI_SCREEN)

        # Check for true color support (Windows 10 1703+)
        if self._supports_true_color():
            capabilities.add(TerminalCapability.TRUE_COLOR)

        # Unicode support is generally available on modern Windows
        capabilities.add(TerminalCapability.UNICODE)

        # Mouse tracking support (limited in conhost)
        # Note: Windows Terminal has better mouse support, but conhost is limited
        if self._supports_mouse_tracking():
            capabilities.add(TerminalCapability.MOUSE_TRACKING)

        # Alternate buffer support (Windows 10 1511+)
        if self._supports_alternate_buffer():
            capabilities.add(TerminalCapability.ALTERNATE_BUFFER)

        self._terminal_info = TerminalInfo(
            terminal_type=TerminalType.CONHOST,
            capabilities=capabilities,
            width=width,
            height=height,
            color_support=TerminalCapability.ANSI_COLORS in capabilities,
            unicode_support=TerminalCapability.UNICODE in capabilities,
            supports_mouse=TerminalCapability.MOUSE_TRACKING in capabilities,
        )

        logger.debug(f"Detected ConHost capabilities: {capabilities}")
        return self._terminal_info

    def _get_terminal_size(self) -> tuple[int, int]:
        """Get terminal size using Windows-specific methods.

        Returns:
            Tuple of (width, height).
        """
        try:
            # Try to get size from environment variables first
            columns = int(os.environ.get("COLUMNS", 80))
            lines = int(os.environ.get("LINES", 24))

            # Use interop subsystem for Windows API access
            try:
                from ornata.api.exports.interop import kernel32

                handle = kernel32.GetStdHandle(kernel32.STD_OUTPUT_HANDLE)

                if handle != 0 and handle is not None:
                    csbi: CsbiStruct = kernel32.CONSOLE_SCREEN_BUFFER_INFO()
                    if kernel32.GetConsoleScreenBufferInfo(handle, csbi):
                        width: int = csbi.srWindow.Right - csbi.srWindow.Left + 1
                        height: int = csbi.srWindow.Bottom - csbi.srWindow.Top + 1
                        return width, height

            except (ImportError, AttributeError, OSError, TypeError):
                pass

            return columns, lines

        except (ValueError, OSError):
            return 80, 24

    def _supports_ansi_screen(self) -> bool:
        """Check if terminal supports ANSI screen buffer operations.

        Returns:
            True if ANSI screen operations are supported.
        """
        # Windows 10 version 1511 (build 10586) added ANSI support
        return self._get_windows_version() >= (10, 0, 10586)

    def _supports_true_color(self) -> bool:
        """Check if terminal supports true color (24-bit).

        Returns:
            True if true color is supported.
        """
        # Windows 10 version 1703 (build 15063) added true color support
        return self._get_windows_version() >= (10, 0, 15063)

    def _supports_mouse_tracking(self) -> bool:
        """Check if terminal supports mouse tracking.

        Returns:
            True if mouse tracking is supported.
        """
        # Mouse tracking is supported in Windows 10, but limited in conhost
        # Windows Terminal has better support, but we assume basic support
        return self._get_windows_version() >= (10, 0, 0)

    def _supports_alternate_buffer(self) -> bool:
        """Check if terminal supports alternate screen buffer.

        Returns:
            True if alternate buffer is supported.
        """
        # Alternate buffer support was added in Windows 10 version 1511
        return self._get_windows_version() >= (10, 0, 10586)

    def _get_windows_version(self) -> tuple[int, int, int]:
        """Get Windows version as (major, minor, build).

        Returns:
            Tuple of (major, minor, build) version numbers.
        """
        try:
            import sys
            if hasattr(sys, 'getwindowsversion'):
                ver = sys.getwindowsversion()
                return (ver.major, ver.minor, ver.build)
        except (AttributeError, OSError):
            pass

        # Fallback: assume Windows 10 if we can't detect
        return (10, 0, 19041)

    def is_available(self) -> bool:
        """Check if this adapter is available on the current system.

        Returns:
            True if running on Windows with Console Host.
        """
        return os.name == 'nt' and self._is_conhost()

    def _is_conhost(self) -> bool:
        """Check if we're running in Windows Console Host.

        Returns:
            True if running in conhost.exe.
        """
        try:
            # Check for Windows Terminal environment variables
            # If WT_SESSION is set, we're in Windows Terminal, not conhost
            if 'WT_SESSION' in os.environ:
                return False

            # Check for conhost-specific environment or process info
            # This is a heuristic - conhost doesn't have unique identifiers
            return True
        except Exception:
            return True  # Assume conhost if we can't determine

    def get_name(self) -> str:
        """Get the adapter name.

        Returns:
            Adapter name string.
        """
        return "conhost"

    def get_version_info(self) -> dict[str, str]:
        """Get version information for this adapter.

        Returns:
            Dictionary with version information.
        """
        major, minor, build = self._get_windows_version()
        return {
            "windows_version": f"{major}.{minor}.{build}",
            "terminal_type": "Windows Console Host",
            "supports_ansi": str(self._supports_ansi_screen()),
            "supports_true_color": str(self._supports_true_color()),
            "supports_mouse": str(self._supports_mouse_tracking()),
        }


# Global adapter instance
_conhost_adapter = ConHostAdapter()


def get_terminal_size() -> tuple[int, int]:
    """Get the current terminal size.

    Returns:
        Tuple of (width, height) in characters.
    """
    return _conhost_adapter._get_terminal_size()


def get_conhost_adapter() -> ConHostAdapter:
    """Get the global ConHost adapter instance.

    Returns:
        ConHostAdapter instance.
    """
    return _conhost_adapter


def detect_conhost_capabilities() -> TerminalInfo:
    """Detect Windows Console Host capabilities.

    Returns:
        TerminalInfo with detected capabilities.
    """
    return _conhost_adapter.detect_capabilities()


def is_conhost_available() -> bool:
    """Check if ConHost adapter is available.

    Returns:
        True if available.
    """
    return _conhost_adapter.is_available()
