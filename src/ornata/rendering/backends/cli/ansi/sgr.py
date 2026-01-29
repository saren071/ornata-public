"""ANSI escape sequences for Select Graphic Rendition (SGR) text formatting.

This module provides functions to generate ANSI escape sequences for text
formatting operations like bold, italic, underline, strikethrough, etc.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.api.exports.definitions import (
    CSI,
    SGR_BLINK,
    SGR_BOLD,
    SGR_DIM,
    SGR_FRAKTUR,
    SGR_HIDDEN,
    SGR_ITALIC,
    SGR_RAPID_BLINK,
    SGR_RESET_ALL,
    SGR_RESET_BLINK,
    SGR_RESET_BOLD_DIM,
    SGR_RESET_HIDDEN,
    SGR_RESET_ITALIC,
    SGR_RESET_REVERSE,
    SGR_RESET_STRIKETHROUGH,
    SGR_RESET_UNDERLINE,
    SGR_REVERSE,
    SGR_STRIKETHROUGH,
    SGR_SUBSCRIPT,
    SGR_SUPERSCRIPT,
    SGR_UNDERLINE,
    SGR_UNDERLINE_DOUBLE,
)

if TYPE_CHECKING:
    from ornata.api.exports.definitions import TextStyle


def sgr_code(code: int) -> str:
    """Generate SGR sequence for a single code.

    Args:
        code: SGR code number.

    Returns:
        ANSI escape sequence string.
    """
    return f"{CSI}{code}m"


def sgr_codes(codes: list[int]) -> str:
    """Generate SGR sequence for multiple codes.

    Args:
        codes: List of SGR code numbers.

    Returns:
        ANSI escape sequence string.
    """
    if not codes:
        return ""
    code_str = ";".join(str(code) for code in codes)
    return f"{CSI}{code_str}m"


def reset_all() -> str:
    """Generate sequence to reset all text formatting.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_RESET_ALL)


def bold() -> str:
    """Generate sequence to enable bold text.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_BOLD)


def dim() -> str:
    """Generate sequence to enable dim (faint) text.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_DIM)


def italic() -> str:
    """Generate sequence to enable italic text.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_ITALIC)


def underline() -> str:
    """Generate sequence to enable underlined text.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_UNDERLINE)


def blink() -> str:
    """Generate sequence to enable blinking text.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_BLINK)


def rapid_blink() -> str:
    """Generate sequence to enable rapid blinking text.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_RAPID_BLINK)


def reverse() -> str:
    """Generate sequence to enable reverse video (swap foreground/background).

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_REVERSE)


def hidden() -> str:
    """Generate sequence to enable hidden text.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_HIDDEN)


def strikethrough() -> str:
    """Generate sequence to enable strikethrough text.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_STRIKETHROUGH)


def reset_bold_dim() -> str:
    """Generate sequence to reset bold/dim attributes.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_RESET_BOLD_DIM)


def reset_italic() -> str:
    """Generate sequence to reset italic attribute.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_RESET_ITALIC)


def reset_underline() -> str:
    """Generate sequence to reset underline attribute.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_RESET_UNDERLINE)


def reset_blink() -> str:
    """Generate sequence to reset blink attribute.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_RESET_BLINK)


def reset_reverse() -> str:
    """Generate sequence to reset reverse video attribute.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_RESET_REVERSE)


def reset_hidden() -> str:
    """Generate sequence to reset hidden attribute.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_RESET_HIDDEN)


def reset_strikethrough() -> str:
    """Generate sequence to reset strikethrough attribute.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_RESET_STRIKETHROUGH)


def font_select(font_num: int) -> str:
    """Generate sequence to select alternate font.

    Args:
        font_num: Font number (0=primary, 1-9=alternate fonts).

    Returns:
        ANSI escape sequence string.

    Raises:
        ValueError: If font_num is not in range 0-9.
    """
    if not (0 <= font_num <= 9):
        raise ValueError("Font number must be 0-9")
    return sgr_code(10 + font_num)


def underline_double() -> str:
    """Generate sequence to enable double underline.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_UNDERLINE_DOUBLE)


def fraktur() -> str:
    """Generate sequence to enable Fraktur (gothic) font.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_FRAKTUR)


def superscript() -> str:
    """Generate sequence to enable superscript.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_SUPERSCRIPT)


def subscript() -> str:
    """Generate sequence to enable subscript.

    Returns:
        ANSI escape sequence string.
    """
    return sgr_code(SGR_SUBSCRIPT)


def style_from_text_style(style: TextStyle) -> str:
    """Generate SGR sequence from TextStyle object.

    Args:
        style: TextStyle object with formatting attributes.

    Returns:
        ANSI escape sequence string.
    """
    codes: list[int] = []

    if style.bold:
        codes.append(SGR_BOLD)
    if style.italic:
        codes.append(SGR_ITALIC)
    if style.underline:
        codes.append(SGR_UNDERLINE)
    if style.strikethrough:
        codes.append(SGR_STRIKETHROUGH)
    if style.blink:
        codes.append(SGR_BLINK)
    if style.reverse:
        codes.append(SGR_REVERSE)

    return sgr_codes(codes)


def combine_styles(*styles: str) -> str:
    """Combine multiple SGR style sequences.

    Args:
        *styles: Variable number of SGR style strings.

    Returns:
        Combined ANSI escape sequence string.
    """
    return "".join(styles)


__all__ = [
    "blink",
    "bold",
    "combine_styles",
    "dim",
    "font_select",
    "fraktur",
    "hidden",
    "italic",
    "rapid_blink",
    "reset_all",
    "reset_blink",
    "reset_bold_dim",
    "reset_hidden",
    "reset_italic",
    "reset_reverse",
    "reset_strikethrough",
    "reset_underline",
    "reverse",
    "sgr_code",
    "sgr_codes",
    "strikethrough",
    "style_from_text_style",
    "subscript",
    "superscript",
    "underline",
    "underline_double"
]
