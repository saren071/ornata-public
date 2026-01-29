"""ANSI escape sequences for color palette management.

This module provides functions to generate ANSI escape sequences for color
control operations, including 16-color, 256-color, and true color support.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.api.exports.definitions import ANSI_16_BACKGROUND, ANSI_16_COLORS, ANSI_16_FOREGROUND, CSI, RESET_ALL, RESET_BACKGROUND, RESET_FOREGROUND

if TYPE_CHECKING:
    from ornata.api.exports.definitions import ANSIColor


def ansi_16_foreground(color_code: int) -> str:
    """Generate ANSI 16-color foreground sequence.

    Args:
        color_code: Color code (0-15).

    Returns:
        ANSI escape sequence string.

    Raises:
        ValueError: If color_code is not in range 0-15.
    """
    if not (0 <= color_code <= 15):
        raise ValueError("Color code must be 0-15 for ANSI 16 colors")
    return ANSI_16_FOREGROUND[color_code]


def ansi_16_background(color_code: int) -> str:
    """Generate ANSI 16-color background sequence.

    Args:
        color_code: Color code (0-15).

    Returns:
        ANSI escape sequence string.

    Raises:
        ValueError: If color_code is not in range 0-15.
    """
    if not (0 <= color_code <= 15):
        raise ValueError("Color code must be 0-15 for ANSI 16 colors")
    return ANSI_16_BACKGROUND[color_code]


def ansi_16_by_name(name: str, bright: bool = False, background: bool = False) -> str:
    """Generate ANSI 16-color sequence by color name.

    Args:
        name: Color name ("black", "red", "green", etc.).
        bright: Whether to use bright variant.
        background: Whether to set background instead of foreground.

    Returns:
        ANSI escape sequence string.

    Raises:
        ValueError: If color name is not recognized.
    """
    name = name.lower()
    if name not in ANSI_16_COLORS:
        raise ValueError(f"Unknown color name: {name}")

    base_code = ANSI_16_COLORS[name]
    color_code = base_code + (8 if bright else 0)

    if background:
        return ansi_16_background(color_code)
    else:
        return ansi_16_foreground(color_code)


def ansi_256_foreground(color_code: int) -> str:
    """Generate ANSI 256-color foreground sequence.

    Args:
        color_code: Color code (0-255).

    Returns:
        ANSI escape sequence string.

    Raises:
        ValueError: If color_code is not in range 0-255.
    """
    if not (0 <= color_code <= 255):
        raise ValueError("Color code must be 0-255 for ANSI 256 colors")
    return f"{CSI}38;5;{color_code}m"


def ansi_256_background(color_code: int) -> str:
    """Generate ANSI 256-color background sequence.

    Args:
        color_code: Color code (0-255).

    Returns:
        ANSI escape sequence string.

    Raises:
        ValueError: If color_code is not in range 0-255.
    """
    if not (0 <= color_code <= 255):
        raise ValueError("Color code must be 0-255 for ANSI 256 colors")
    return f"{CSI}48;5;{color_code}m"


def true_color_foreground(color: ANSIColor) -> str:
    """Generate true color (24-bit) foreground sequence.

    Args:
        color: ANSIColor object with RGB values.

    Returns:
        ANSI escape sequence string.
    """
    return f"{CSI}38;2;{color.red};{color.green};{color.blue}m"


def true_color_background(color: ANSIColor) -> str:
    """Generate true color (24-bit) background sequence.

    Args:
        color: ANSIColor object with RGB values.

    Returns:
        ANSI escape sequence string.
    """
    return f"{CSI}48;2;{color.red};{color.green};{color.blue}m"


def color_foreground(color: ANSIColor, color_mode: str = "256") -> str:
    """Generate foreground color sequence for given color and mode.

    Args:
        color: ANSIColor object.
        color_mode: Color mode ("16", "256", or "truecolor").

    Returns:
        ANSI escape sequence string.

    Raises:
        ValueError: If color_mode is not supported.
    """
    color_mode = color_mode.lower()
    if color_mode == "16":
        return ansi_16_foreground(color.to_ansi_16())
    elif color_mode == "256":
        return ansi_256_foreground(color.to_ansi_256())
    elif color_mode == "truecolor":
        return true_color_foreground(color)
    else:
        raise ValueError(f"Unsupported color mode: {color_mode}")


def color_background(color: ANSIColor, color_mode: str = "256") -> str:
    """Generate background color sequence for given color and mode.

    Args:
        color: ANSIColor object.
        color_mode: Color mode ("16", "256", or "truecolor").

    Returns:
        ANSI escape sequence string.

    Raises:
        ValueError: If color_mode is not supported.
    """
    color_mode = color_mode.lower()
    if color_mode == "16":
        return ansi_16_background(color.to_ansi_16())
    elif color_mode == "256":
        return ansi_256_background(color.to_ansi_256())
    elif color_mode == "truecolor":
        return true_color_background(color)
    else:
        raise ValueError(f"Unsupported color mode: {color_mode}")


def reset_colors() -> str:
    """Generate sequence to reset all color attributes.

    Returns:
        ANSI escape sequence string.
    """
    return RESET_ALL


def reset_foreground() -> str:
    """Generate sequence to reset foreground color to default.

    Returns:
        ANSI escape sequence string.
    """
    return RESET_FOREGROUND


def reset_background() -> str:
    """Generate sequence to reset background color to default.

    Returns:
        ANSI escape sequence string.
    """
    return RESET_BACKGROUND


def set_default_colors(fg: ANSIColor | None = None, bg: ANSIColor | None = None, color_mode: str = "256") -> str:
    """Generate sequence to set default colors.

    Args:
        fg: Default foreground color (None to reset).
        bg: Default background color (None to reset).
        color_mode: Color mode for ANSIColor conversion.

    Returns:
        ANSI escape sequence string.
    """
    sequences: list[str] = []

    if fg is not None:
        sequences.append(color_foreground(fg, color_mode))
    else:
        sequences.append(reset_foreground())

    if bg is not None:
        sequences.append(color_background(bg, color_mode))
    else:
        sequences.append(reset_background())

    return "".join(sequences)


# Predefined color constants for common use


__all__ = [
    "ansi_16_background",
    "ansi_16_by_name",
    "ansi_16_foreground",
    "ansi_256_background",
    "ansi_256_foreground",
    "color_background",
    "color_foreground",
    "reset_background",
    "reset_colors",
    "reset_foreground",
    "set_default_colors",
    "true_color_background",
    "true_color_foreground",
]
