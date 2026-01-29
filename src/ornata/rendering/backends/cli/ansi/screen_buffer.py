"""ANSI escape sequences for screen buffer management.

This module provides functions to generate ANSI escape sequences for screen
buffer operations like clearing, scrolling, and alternate buffer management.
"""

from __future__ import annotations

from ornata.api.exports.definitions import CLEAR_LINE, CLEAR_LINE_FROM_CURSOR, CLEAR_LINE_TO_CURSOR, CLEAR_SCREEN, CLEAR_SCREEN_FROM_CURSOR, CLEAR_SCREEN_TO_CURSOR, CSI, ENTER_ALTERNATE_BUFFER, EXIT_ALTERNATE_BUFFER, SCROLL_DOWN, SCROLL_UP


def clear_screen() -> str:
    """Generate sequence to clear entire screen.

    Returns:
        ANSI escape sequence string.
    """
    return CLEAR_SCREEN


def clear_screen_from_cursor() -> str:
    """Generate sequence to clear screen from cursor to end.

    Returns:
        ANSI escape sequence string.
    """
    return CLEAR_SCREEN_FROM_CURSOR


def clear_screen_to_cursor() -> str:
    """Generate sequence to clear screen from beginning to cursor.

    Returns:
        ANSI escape sequence string.
    """
    return CLEAR_SCREEN_TO_CURSOR


def clear_line() -> str:
    """Generate sequence to clear entire current line.

    Returns:
        ANSI escape sequence string.
    """
    return CLEAR_LINE


def clear_line_from_cursor() -> str:
    """Generate sequence to clear line from cursor to end of line.

    Returns:
        ANSI escape sequence string.
    """
    return CLEAR_LINE_FROM_CURSOR


def clear_line_to_cursor() -> str:
    """Generate sequence to clear line from beginning to cursor.

    Returns:
        ANSI escape sequence string.
    """
    return CLEAR_LINE_TO_CURSOR


def enter_alternate_buffer() -> str:
    """Generate sequence to switch to alternate screen buffer.

    Returns:
        ANSI escape sequence string.
    """
    return ENTER_ALTERNATE_BUFFER


def exit_alternate_buffer() -> str:
    """Generate sequence to switch back to main screen buffer.

    Returns:
        ANSI escape sequence string.
    """
    return EXIT_ALTERNATE_BUFFER


def scroll_up(lines: int = 1) -> str:
    """Generate sequence to scroll screen up by specified lines.

    Args:
        lines: Number of lines to scroll up (default: 1).

    Returns:
        ANSI escape sequence string.

    Raises:
        ValueError: If lines is not positive.
    """
    if lines < 1:
        raise ValueError("Lines must be positive")
    if lines == 1:
        return SCROLL_UP
    return f"{CSI}{lines}S"


def scroll_down(lines: int = 1) -> str:
    """Generate sequence to scroll screen down by specified lines.

    Args:
        lines: Number of lines to scroll down (default: 1).

    Returns:
        ANSI escape sequence string.

    Raises:
        ValueError: If lines is not positive.
    """
    if lines < 1:
        raise ValueError("Lines must be positive")
    if lines == 1:
        return SCROLL_DOWN
    return f"{CSI}{lines}T"


def erase_in_display(mode: int = 0) -> str:
    """Generate sequence to erase part of display.

    Args:
        mode: Erase mode (0=cursor to end, 1=beginning to cursor, 2=entire screen).

    Returns:
        ANSI escape sequence string.

    Raises:
        ValueError: If mode is not 0, 1, or 2.
    """
    if mode not in (0, 1, 2):
        raise ValueError("Mode must be 0, 1, or 2")
    return f"{CSI}{mode}J"


def erase_in_line(mode: int = 0) -> str:
    """Generate sequence to erase part of current line.

    Args:
        mode: Erase mode (0=cursor to end, 1=beginning to cursor, 2=entire line).

    Returns:
        ANSI escape sequence string.

    Raises:
        ValueError: If mode is not 0, 1, or 2.
    """
    if mode not in (0, 1, 2):
        raise ValueError("Mode must be 0, 1, or 2")
    return f"{CSI}{mode}K"


def set_scroll_region(top: int = 1, bottom: int | None = None) -> str:
    """Generate sequence to set scrolling region.

    Args:
        top: Top line of scroll region (1-based, default: 1).
        bottom: Bottom line of scroll region (1-based, None for screen height).

    Returns:
        ANSI escape sequence string.

    Raises:
        ValueError: If top is not positive or bottom is specified and <= top.
    """
    if top < 1:
        raise ValueError("Top must be positive")
    if bottom is not None and bottom <= top:
        raise ValueError("Bottom must be greater than top")

    if bottom is None:
        return f"{CSI}{top}r"
    else:
        return f"{CSI}{top};{bottom}r"


def reset_scroll_region() -> str:
    """Generate sequence to reset scrolling region to full screen.

    Returns:
        ANSI escape sequence string.
    """
    return f"{CSI}r"


def insert_lines(lines: int = 1) -> str:
    """Generate sequence to insert blank lines at cursor position.

    Args:
        lines: Number of lines to insert (default: 1).

    Returns:
        ANSI escape sequence string.

    Raises:
        ValueError: If lines is not positive.
    """
    if lines < 1:
        raise ValueError("Lines must be positive")
    return f"{CSI}{lines}L"


def delete_lines(lines: int = 1) -> str:
    """Generate sequence to delete lines at cursor position.

    Args:
        lines: Number of lines to delete (default: 1).

    Returns:
        ANSI escape sequence string.

    Raises:
        ValueError: If lines is not positive.
    """
    if lines < 1:
        raise ValueError("Lines must be positive")
    return f"{CSI}{lines}M"


def insert_chars(chars: int = 1) -> str:
    """Generate sequence to insert blank characters at cursor position.

    Args:
        chars: Number of characters to insert (default: 1).

    Returns:
        ANSI escape sequence string.

    Raises:
        ValueError: If chars is not positive.
    """
    if chars < 1:
        raise ValueError("Chars must be positive")
    return f"{CSI}{chars}@"


def delete_chars(chars: int = 1) -> str:
    """Generate sequence to delete characters at cursor position.

    Args:
        chars: Number of characters to delete (default: 1).

    Returns:
        ANSI escape sequence string.

    Raises:
        ValueError: If chars is not positive.
    """
    if chars < 1:
        raise ValueError("Chars must be positive")
    return f"{CSI}{chars}P"


def set_window_title(title: str) -> str:
    """Generate sequence to set window title (OSC 2).

    Args:
        title: Window title string.

    Returns:
        ANSI escape sequence string.
    """
    # OSC 2 ; title ST
    return f"\x1b]2;{title}\x1b\\"


def bell() -> str:
    """Generate sequence to ring the terminal bell.

    Returns:
        ANSI escape sequence string.
    """
    return "\x07"


def report_device_attributes(primary: bool = True) -> str:
    """Generate sequence to query terminal device attributes.

    Args:
        primary: Whether to request primary (True) or secondary (False) attributes.

    Returns:
        ANSI escape sequence string.
    """
    if primary:
        return f"{CSI}c"  # Primary DA
    else:
        return f"{CSI}>c"  # Secondary DA


def report_cursor_position() -> str:
    """Generate sequence to query current cursor position.

    Returns:
        ANSI escape sequence string.
    """
    return f"{CSI}6n"


def report_window_size() -> str:
    """Generate sequence to query window size (xterm extension).

    Returns:
        ANSI escape sequence string.
    """
    return f"{CSI}14t"


def enable_alternate_screen_buffer() -> str:
    """Generate sequence to enable alternate screen buffer.

    Returns:
        ANSI escape sequence string.
    """
    return enter_alternate_buffer()


def disable_alternate_screen_buffer() -> str:
    """Generate sequence to disable alternate screen buffer.

    Returns:
        ANSI escape sequence string.
    """
    return exit_alternate_buffer()


__all__ = [
    "bell",
    "clear_line",
    "clear_line_from_cursor",
    "clear_line_to_cursor",
    "clear_screen",
    "clear_screen_from_cursor",
    "clear_screen_to_cursor",
    "delete_chars",
    "delete_lines",
    "disable_alternate_screen_buffer",
    "enable_alternate_screen_buffer",
    "enter_alternate_buffer",
    "erase_in_display",
    "erase_in_line",
    "exit_alternate_buffer",
    "insert_chars",
    "insert_lines",
    "report_cursor_position",
    "report_device_attributes",
    "report_window_size",
    "reset_scroll_region",
    "scroll_down",
    "scroll_up",
    "set_scroll_region",
    "set_window_title",
]
