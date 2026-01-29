"""ANSI conversion helpers tailored for the Ornata styling system."""

from __future__ import annotations


class AnsiConverter:
    """Utility helpers for converting color specifications to ANSI codes."""

    # Lazily-cached fast paths to avoid per-call hasattr checks
    _fast_rgb_to_ansi = None
    _fast_rgb_to_bg_ansi = None
    _fast_hex_to_rgb = None
    _fast_parse_rgb_string = None
    _fast_rgb_str_to_ansi = None
    _fast_rgb_str_to_bg_ansi = None
    _fast_hex_to_ansi = None
    _fast_hex_to_bg_ansi = None

    @staticmethod
    def rgb_to_ansi(rgb: tuple[int, int, int]) -> str:
        """Return the ANSI escape sequence for a 24-bit RGB color."""
        fast = AnsiConverter._fast_rgb_to_ansi
        if fast:
            return str(fast(int(rgb[0]), int(rgb[1]), int(rgb[2])))

        r, g, b = rgb
        # inline clamp avoids generator allocation + attribute lookup
        r = 0 if r < 0 else (255 if r > 255 else int(r))
        g = 0 if g < 0 else (255 if g > 255 else int(g))
        b = 0 if b < 0 else (255 if b > 255 else int(b))
        # f-string is faster than str.format with named fields
        return f"\033[38;2;{r};{g};{b}m"

    @staticmethod
    def rgb_to_bg_ansi(rgb: tuple[int, int, int]) -> str:
        """Return the ANSI escape sequence for a background 24-bit RGB color."""
        fast = AnsiConverter._fast_rgb_to_bg_ansi
        if fast:
            return str(fast(int(rgb[0]), int(rgb[1]), int(rgb[2])))

        r, g, b = rgb
        r = 0 if r < 0 else (255 if r > 255 else int(r))
        g = 0 if g < 0 else (255 if g > 255 else int(g))
        b = 0 if b < 0 else (255 if b > 255 else int(b))
        return f"\033[48;2;{r};{g};{b}m"

    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple[int, int, int] | None:
        """Convert a #RRGGBB string to an RGB tuple."""
        fast = AnsiConverter._fast_hex_to_rgb
        if fast:
            parsed = fast(hex_color)
            if parsed is None:
                return None
            r, g, b = int(parsed[0]), int(parsed[1]), int(parsed[2])
            # values from C path are already in range
            return (r, g, b)

        s = hex_color.strip()
        if s.startswith("#"):
            s = s[1:]
        if len(s) != 6:
            return None
        try:
            v = int(s, 16)
        except ValueError:
            return None
        return ((v >> 16) & 255, (v >> 8) & 255, v & 255)

    @staticmethod
    def hex_to_ansi(hex_color: str) -> str:
        """Return the ANSI escape sequence for a #RRGGBB colour.

        Args:
            hex_color (str): Colour in hexadecimal notation.

        Returns:
            str: Foreground ANSI escape code, or an empty string when parsing fails.
        """

        rgb = AnsiConverter.hex_to_rgb(hex_color)
        return AnsiConverter.rgb_to_ansi(rgb) if rgb else ""

    @staticmethod
    def hex_to_bg_ansi(hex_color: str) -> str:
        """Return the background ANSI escape for a #RRGGBB colour.

        Args:
            hex_color (str): Colour in hexadecimal notation.

        Returns:
            str: Background ANSI escape code, or an empty string when parsing fails.
        """

        rgb = AnsiConverter.hex_to_rgb(hex_color)
        return AnsiConverter.rgb_to_bg_ansi(rgb) if rgb else ""

    @staticmethod
    def parse_rgb_string(rgb_color: str) -> tuple[int, int, int] | None:
        """Parse 'r,g,b' formatted text into an RGB tuple."""
        fast = AnsiConverter._fast_parse_rgb_string
        if fast:
            parsed = fast(rgb_color)
            if parsed is None:
                return None
            return (int(parsed[0]), int(parsed[1]), int(parsed[2]))

        parts = rgb_color.split(",", 2)
        if len(parts) != 3:
            return None
        try:
            r = int(parts[0].strip())
            g = int(parts[1].strip())
            b = int(parts[2].strip())
        except ValueError:
            return None
        # inline clamp
        r = 0 if r < 0 else (255 if r > 255 else r)
        g = 0 if g < 0 else (255 if g > 255 else g)
        b = 0 if b < 0 else (255 if b > 255 else b)
        return (r, g, b)

    @staticmethod
    def rgb_str_to_ansi(rgb_color: str) -> str:
        """Return the ANSI escape sequence for a 'r,g,b' colour string.

        Args:
            rgb_color (str): Comma-delimited RGB components.

        Returns:
            str: Foreground ANSI escape, or an empty string when parsing fails.
        """

        rgb = AnsiConverter.parse_rgb_string(rgb_color)
        return AnsiConverter.rgb_to_ansi(rgb) if rgb else ""

    @staticmethod
    def rgb_str_to_bg_ansi(rgb_color: str) -> str:
        """Return the background ANSI escape sequence for a 'r,g,b' colour string.

        Args:
            rgb_color (str): Comma-delimited RGB components.

        Returns:
            str: Background ANSI escape, or an empty string when parsing fails.
        """

        rgb = AnsiConverter.parse_rgb_string(rgb_color)
        return AnsiConverter.rgb_to_bg_ansi(rgb) if rgb else ""

    @staticmethod
    def _clamp_component(value: int) -> int:
        """Clamp a colour component to the 0-255 range.

        Args:
            value (int): Candidate colour component.

        Returns:
            int: Clamped component within the 0-255 range.
        """

        return max(0, min(255, int(value)))


__all__ = ["AnsiConverter"]
