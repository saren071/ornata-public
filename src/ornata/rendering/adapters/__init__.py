"""VDOM-Renderer adapter layer for seamless VDOM integration.

This module provides adapter layers that translate VDOM tree structures
into renderer-specific primitives for CLI, GUI, and TTY renderers.
"""

from __future__ import annotations

from ornata.api.exports.definitions import BackendTarget
from ornata.api.exports.utils import get_logger

from .base import AdapterFactory, VDOMAdapter
from .cli import CLIAdapter
from .gui import GUIAdapter
from .tty import TTYAdapter

logger = get_logger(__name__)

# Auto-register all adapters
AdapterFactory.register_adapter(BackendTarget.CLI, CLIAdapter)
AdapterFactory.register_adapter(BackendTarget.GUI, GUIAdapter)
AdapterFactory.register_adapter(BackendTarget.TTY, TTYAdapter)

logger.debug("VDOM adapters registered: CLI, GUI, TTY")

__all__ = [
    "VDOMAdapter",
    "AdapterFactory", 
    "CLIAdapter",
    "GUIAdapter",
    "TTYAdapter"
]