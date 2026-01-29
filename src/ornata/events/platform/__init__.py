"""Auto-generated exports for ornata.events.platform."""

from __future__ import annotations

from . import cli, factory, windows
from .cli import (
    CliEventHandler,
    create_cli_handler,
)
from .factory import (
    create_platform_handler,
)
from .windows import (
    WindowsEventHandler,
    create_windows_handler,
)

__all__ = [
    "CliEventHandler",
    "WindowsEventHandler",
    "cli",
    "create_cli_handler",
    "create_platform_handler",
    "create_windows_handler",
    "factory",
    "windows",
]
