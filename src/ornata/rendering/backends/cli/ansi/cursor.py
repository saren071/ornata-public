"""ANSI escape sequences for cursor positioning and movement.

This module provides functions to generate ANSI escape sequences for cursor
control operations used by CLI renderers.
"""

from __future__ import annotations

from ornata.api.exports.definitions import CSI, CURSOR_BAR, CURSOR_BLOCK, CURSOR_DOWN, CURSOR_HIDE, CURSOR_HOME, CURSOR_LEFT, CURSOR_RESTORE, CURSOR_RIGHT, CURSOR_SAVE, CURSOR_SHOW, CURSOR_UNDERLINE, CURSOR_UP, CursorPosition


def cursor_move_up(lines: int = 1) -> str:
    """Generate sequence to move cursor up by specified lines.

    Args:
        lines: Number of lines to move up (default: 1).

    Returns:
        ANSI escape sequence string.
    """
    if lines < 1:
        raise ValueError("Lines must be positive")
    if lines == 1:
        return CURSOR_UP
    return f"{CSI}{lines}A"


def cursor_move_down(lines: int = 1) -> str:
    """Generate sequence to move cursor down by specified lines.

    Args:
        lines: Number of lines to move down (default: 1).

    Returns:
        ANSI escape sequence string.
    """
    if lines < 1:
        raise ValueError("Lines must be positive")
    if lines == 1:
        return CURSOR_DOWN
    return f"{CSI}{lines}B"


def cursor_move_right(cols: int = 1) -> str:
    """Generate sequence to move cursor right by specified columns.

    Args:
        cols: Number of columns to move right (default: 1).

    Returns:
        ANSI escape sequence string.
    """
    if cols < 1:
        raise ValueError("Columns must be positive")
    if cols == 1:
        return CURSOR_RIGHT
    return f"{CSI}{cols}C"


def cursor_move_left(cols: int = 1) -> str:
    """Generate sequence to move cursor left by specified columns.

    Args:
        cols: Number of columns to move left (default: 1).

    Returns:
        ANSI escape sequence string.
    """
    if cols < 1:
        raise ValueError("Columns must be positive")
    if cols == 1:
        return CURSOR_LEFT
    return f"{CSI}{cols}D"


def cursor_position(row: int = 1, col: int = 1) -> str:
    """Generate sequence to move cursor to specific position.

    Args:
        row: Row number (1-based, default: 1).
        col: Column number (1-based, default: 1).

    Returns:
        ANSI escape sequence string.
    """
    if row < 1 or col < 1:
        raise ValueError("Row and column must be positive")
    if row == 1 and col == 1:
        return CURSOR_HOME
    return f"{CSI}{row};{col}H"


def cursor_position_from(pos: CursorPosition) -> str:
    """Generate sequence to move cursor to position from CursorPosition.

    Args:
        pos: Cursor position object.

    Returns:
        ANSI escape sequence string.
    """
    return cursor_position(pos.row + 1, pos.col + 1)  # Convert 0-based to 1-based


def cursor_save_position() -> str:
    """Generate sequence to save current cursor position.

    Returns:
        ANSI escape sequence string.
    """
    return CURSOR_SAVE


def cursor_restore_position() -> str:
    """Generate sequence to restore previously saved cursor position.

    Returns:
        ANSI escape sequence string.
    """
    return CURSOR_RESTORE


def cursor_hide() -> str:
    """Generate sequence to hide the cursor.

    Returns:
        ANSI escape sequence string.
    """
    return CURSOR_HIDE


def cursor_show() -> str:
    """Generate sequence to show the cursor.

    Returns:
        ANSI escape sequence string.
    """
    return CURSOR_SHOW


def cursor_set_style(style: str) -> str:
    """Generate sequence to set cursor style (block, underline, or bar).

    Args:
        style: Cursor style ("block", "underline", or "bar").

    Returns:
        ANSI escape sequence string.

    Raises:
        ValueError: If style is not recognized.
    """
    style = style.lower()
    if style == "block":
        return CURSOR_BLOCK
    elif style == "underline":
        return CURSOR_UNDERLINE
    elif style == "bar":
        return CURSOR_BAR
    else:
        raise ValueError(f"Unknown cursor style: {style}")


def cursor_next_line(lines: int = 1) -> str:
    """Generate sequence to move cursor to beginning of next line(s).

    Args:
        lines: Number of lines to move down (default: 1).

    Returns:
        ANSI escape sequence string.
    """
    if lines < 1:
        raise ValueError("Lines must be positive")
    return f"{CSI}{lines}E"


def cursor_prev_line(lines: int = 1) -> str:
    """Generate sequence to move cursor to beginning of previous line(s).

    Args:
        lines: Number of lines to move up (default: 1).

    Returns:
        ANSI escape sequence string.
    """
    if lines < 1:
        raise ValueError("Lines must be positive")
    return f"{CSI}{lines}F"


def cursor_column(col: int = 1) -> str:
    """Generate sequence to move cursor to specified column on current line.

    Args:
        col: Column number (1-based, default: 1).

    Returns:
        ANSI escape sequence string.
    """
    if col < 1:
        raise ValueError("Column must be positive")
    return f"{CSI}{col}G"


def cursor_get_position() -> str:
    """Generate sequence to query current cursor position.

    Note: This sends a query that terminals respond to with position info.
    The response format is ESC[{row};{col}R

    Returns:
        ANSI escape sequence string to query position.
    """
    return f"{CSI}6n"


def parse_cursor_position_response(response: str) -> CursorPosition | None:
    """Parse cursor position response from terminal.

    Args:
        response: Raw response string from terminal (e.g., "\x1b[24;80R").

    Returns:
        CursorPosition if successfully parsed, None otherwise.
    """
    if not response.startswith("\x1b[") or not response.endswith("R"):
        return None

    try:
        coords = response[2:-1].split(";")
        if len(coords) != 2:
            return None

        row = int(coords[0]) - 1  # Convert from 1-based to 0-based
        col = int(coords[1]) - 1  # Convert from 1-based to 0-based

        if row < 0 or col < 0:
            return None

        return CursorPosition(row=row, col=col)
    except (ValueError, IndexError):
        return None


def cursor_scroll_up(lines: int = 1) -> str:
    """Generate sequence to scroll screen up by specified lines.

    Args:
        lines: Number of lines to scroll up (default: 1).

    Returns:
        ANSI escape sequence string.
    """
    if lines < 1:
        raise ValueError("Lines must be positive")
    return f"{CSI}{lines}S"


def cursor_scroll_down(lines: int = 1) -> str:
    """Generate sequence to scroll screen down by specified lines.

    Args:
        lines: Number of lines to scroll down (default: 1).

    Returns:
        ANSI escape sequence string.
    """
    if lines < 1:
        raise ValueError("Lines must be positive")
    return f"{CSI}{lines}T"


__all__ = [
    "cursor_column",
    "cursor_get_position",
    "cursor_hide",
    "cursor_move_down",
    "cursor_move_left",
    "cursor_move_right",
    "cursor_move_up",
    "cursor_next_line",
    "cursor_position",
    "cursor_position_from",
    "cursor_prev_line",
    "cursor_restore_position",
    "cursor_save_position",
    "cursor_scroll_down",
    "cursor_scroll_up",
    "cursor_set_style",
    "cursor_show",
    "parse_cursor_position_response",
]
