"""Platform-specific event handlers for the event system.

This module provides platform detection and handler creation for different
operating systems and environments.
"""

from __future__ import annotations

import platform

from ornata.api.exports.definitions import PlatformEventHandler
from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


def create_platform_handler() -> PlatformEventHandler | None:
    """Create an appropriate platform event handler for the current system.

    Returns:
        PlatformEventHandler | None: Handler instance for the current platform,
        or None if no suitable handler is available.
    """
    system = platform.system().lower()

    # Try platform-specific handlers in order of preference
    if system == "windows":
        try:
            from ornata.events.platform import create_windows_handler
            handler = create_windows_handler()
            if handler.is_available():
                logger.debug("Using Windows event handler")
                return handler
        except ImportError as exc:
            logger.debug("Windows handler not available: %s", exc)

    # Fallback to CLI handler for any platform
    try:
        from ornata.events.platform import create_cli_handler
        handler = create_cli_handler()
        if handler.is_available():
            logger.debug("Using CLI event handler")
            return handler
    except ImportError as exc:
        logger.debug("CLI handler not available: %s", exc)

    logger.warning("No suitable platform event handler found for %s", system)
    return None


# Export platform handlers for direct use
__all__ = ["PlatformEventHandler", "create_platform_handler"]
