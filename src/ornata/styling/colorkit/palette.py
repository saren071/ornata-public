"""Palette data and helpers for the Ornata colour system."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ornata.definitions.dataclasses.styling import PaletteEntry


class PaletteLibrary:
    """Central storage for named colours, background codes, and text effects."""

    # Foreground ANSI shortcuts

    @classmethod
    def get_named_color(cls, name: str) -> str:
        """Return the ANSI escape for a named foreground colour.

        Args:
            name (str): Semantic colour token (case insensitive).

        Returns:
            str: ANSI escape sequence or an empty string when the token is unknown.
        """
        from ornata.styling.colorkit.named_colors import NAMED_COLORS

        return NAMED_COLORS.get(name.lower(), "")

    @classmethod
    def get_named_hex(cls, name: str) -> str | None:
        """Return the canonical hex value for a named colour.

        Args:
            name (str): Semantic colour token (case insensitive).

        Returns:
            str | None: Hex value when available.
        """
        from ornata.styling.colorkit.named_colors import NAMED_COLORS

        return NAMED_COLORS.get(name.lower())

    @classmethod
    def get_background_color(cls, name: str) -> str:
        """Return the ANSI escape for a named background colour.

        Args:
            name (str): Semantic background token such as ``bg_primary``.

        Returns:
            str: ANSI escape sequence or an empty string when the token is unknown.
        """
        from ornata.definitions.constants import BACKGROUND_COLORS

        token = name.lower()
        if not token.startswith("bg_"):
            token = f"bg_{token}"
        return BACKGROUND_COLORS.get(token, "")

    @classmethod
    def get_effect(cls, name: str) -> str:
        """Return the ANSI escape for a text effect token.

        Args:
            name (str): Name of the effect (reset, bold, underline, ...).

        Returns:
            str: ANSI escape sequence or an empty string when the token is unknown.
        """
        from ornata.definitions.constants import EFFECTS

        return EFFECTS.get(name.lower(), "")

    @classmethod
    def register_named_color(cls, entry: PaletteEntry) -> None:
        """Register a new named colour entry.

        Args:
            entry (PaletteEntry): Entry describing the color literal.

        Returns:
            None
        """
        from ornata.styling.colorkit.named_colors import NAMED_COLORS

        token = entry.token.lower()
        # Convert ColorLiteral to hex for storage
        if entry.literal.kind == "hex":
            hex_value = entry.literal.value if isinstance(entry.literal.value, str) else ""
            NAMED_COLORS[token] = hex_value
        elif entry.cached_rgb:
            r, g, b = entry.cached_rgb
            NAMED_COLORS[token] = f"#{r:02x}{g:02x}{b:02x}"
        else:
            rgb = entry.literal.to_rgb()
            if rgb:
                r, g, b = rgb
                NAMED_COLORS[token] = f"#{r:02x}{g:02x}{b:02x}"


__all__ = ["PaletteLibrary"]
