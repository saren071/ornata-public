"""Auto-generated exports for ornata.rendering.backends.cli.platform."""

from __future__ import annotations

from . import conhost, detector
from .conhost import (
    ConHostAdapter,
    detect_conhost_capabilities,
    get_conhost_adapter,
    get_terminal_size,
    is_conhost_available,
)
from .detector import (
    detect_terminal_capabilities,
    get_terminal_adapter,
)

__all__ = [
    "ConHostAdapter",
    "conhost",
    "detect_conhost_capabilities",
    "detect_terminal_capabilities",
    "detector",
    "get_conhost_adapter",
    "get_terminal_adapter",
    "get_terminal_size",
    "is_conhost_available",
]
