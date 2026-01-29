"""Auto-generated exports for ornata.rendering.tty."""

from __future__ import annotations

from . import input, platform, renderer, termios, vt100
from .input import (
    InputReader,
    parse_mouse_event,
)
from .renderer import TTYRenderer
from .termios import (
    TerminalController,
    get_terminal_size,
    is_terminal,
)
from .vt100 import (
    VT100,
    get_text_width,
    strip_ansi,
)

__all__ = [
    "InputReader",
    "TTYRenderer",
    "TerminalController",
    "VT100",
    "get_terminal_size",
    "get_text_width",
    "input",
    "is_terminal",
    "parse_mouse_event",
    "platform",
    "renderer",
    "strip_ansi",
    "termios",
    "vt100",
]
