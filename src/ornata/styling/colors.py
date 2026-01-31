"""High-level colour facade used throughout the Ornata runtime."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.styling.colorkit.resolver import ColorResolver

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ornata.definitions.dataclasses.styling import PaletteEntry
    from ornata.definitions.type_alias import ColorSpec

resolver = ColorResolver()
def _theme_lookup(token: str) -> str | None:
    """Resolve theme tokens lazily to avoid circular imports.

    Args:
        token (str): Theme token without prefix.

    Returns:
        str | None: Resolved colour specification or ``None`` when not defined.
    """

    from ornata.styling.theming.manager import get_theme_manager

    return get_theme_manager().resolve_token(token)


def _theme_version() -> int:
    """Return the active theme version for cache invalidation.

    Returns:
        int: Incrementing theme version identifier.
    """

    from ornata.styling.theming.manager import get_theme_manager

    return get_theme_manager().version

class Color:
    """Facade exposing colour utilities, conversions, and markup helpers."""
    from ornata.styling.colorkit.palette import PaletteLibrary

    @staticmethod
    def register_named_color(entry: PaletteEntry) -> None:
        """Register a custom named colour at runtime.

        Args:
            entry (PaletteEntry): Palette entry describing the colour mapping.

        Returns:
            None
        """
        from ornata.styling.colorkit.palette import PaletteLibrary

        PaletteLibrary.register_named_color(entry)
        resolver.invalidate()

    @staticmethod
    def get_color(color_spec: ColorSpec | None) -> str:
        """Return the ANSI foreground escape sequence for ``color_spec``.

        Args:
            color_spec (ColorSpec | None): Colour specification or theme token.

        Returns:
            str: ANSI escape sequence representing the colour.
        """

        return resolver.resolve_ansi(color_spec)

    @staticmethod
    def get_bg_color(color_spec: str | None) -> str:
        """Return the ANSI background escape sequence for ``color_spec``.

        Args:
            color_spec (str | None): Colour specification or theme token.

        Returns:
            str: ANSI escape sequence for the background colour.
        """

        return resolver.resolve_background(color_spec)

    @staticmethod
    def resolve_rgb(color_spec: ColorSpec | None) -> tuple[int, int, int] | None:
        """Resolve ``color_spec`` to an RGB tuple.

        Args:
            color_spec (ColorSpec | None): Colour specification or theme token.

        Returns:
            tuple[int, int, int] | None: RGB tuple in 0-255 range when resolved.
        """

        return resolver.resolve_rgb(color_spec)

    @staticmethod
    def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        """Return the ``#RRGGBB`` string for ``rgb``.

        Args:
            rgb (tuple[int, int, int]): RGB tuple in 0-255 range.

        Returns:
            str: Hexadecimal representation of the colour.
        """
        from ornata.styling.colorkit.spaces import ColorSpaces

        return ColorSpaces.rgb_to_hex(rgb)

    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple[int, int, int] | None:
        """Convert ``hex_color`` to an RGB tuple.

        Args:
            hex_color (str): Colour in hexadecimal ``#RRGGBB`` format.

        Returns:
            tuple[int, int, int] | None: RGB tuple or ``None`` when parsing fails.
        """
        from ornata.styling.colorkit.ansi import AnsiConverter

        return AnsiConverter.hex_to_rgb(hex_color)

    @staticmethod
    def rgb_to_hsv(r: int, g: int, b: int) -> tuple[float, float, float]:
        """Convert RGB components to HSV (degrees, saturation, value).

        Args:
            r (int): Red component.
            g (int): Green component.
            b (int): Blue component.

        Returns:
            tuple[float, float, float]: HSV tuple (degrees, saturation, value).
        """
        from ornata.styling.colorkit.spaces import ColorSpaces

        return ColorSpaces.rgb_to_hsv((r, g, b))

    @staticmethod
    def hsv_to_rgb(h: float, s: float, v: float) -> tuple[int, ...]:
        """Convert HSV values to an RGB tuple.

        Args:
            h (float): Hue in degrees.
            s (float): Saturation in the 0-1 range.
            v (float): Value in the 0-1 range.

        Returns:
            tuple[int, ...]: RGB tuple in 0-255 range.
        """
        from ornata.styling.colorkit.spaces import ColorSpaces

        return ColorSpaces.hsv_to_rgb((h, s, v))

    @staticmethod
    def rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
        """Convert RGB components to HSL (degrees, saturation, lightness).

        Args:
            r (int): Red component.
            g (int): Green component.
            b (int): Blue component.

        Returns:
            tuple[float, float, float]: HSL tuple (degrees, saturation, lightness).
        """
        from ornata.styling.colorkit.spaces import ColorSpaces

        return ColorSpaces.rgb_to_hsl((r, g, b))

    @staticmethod
    def hsl_to_rgb(h: float, s: float, lightness: float) -> tuple[int, ...]:
        """Convert HSL values to an RGB tuple.

        Args:
            h (float): Hue in degrees.
            s (float): Saturation in the 0-1 range.
            lightness (float): Lightness in the 0-1 range.

        Returns:
            tuple[int, ...]: RGB tuple in 0-255 range.
        """
        from ornata.styling.colorkit.spaces import ColorSpaces

        return ColorSpaces.hsl_to_rgb((h, s, lightness))

    @staticmethod
    def adjust_luminance(rgb: tuple[int, int, int], amount: float) -> tuple[int, ...]:
        """Lighten or darken ``rgb`` by ``amount`` in lightness space.

        Args:
            rgb (tuple[int, int, int]): Source RGB tuple.
            amount (float): Positive to lighten, negative to darken.

        Returns:
            tuple[int, ...]: Adjusted RGB tuple.
        """
        from ornata.styling.colorkit.spaces import ColorSpaces

        return ColorSpaces.adjust_luminance(rgb, amount)

    @staticmethod
    def blend(rgb_a: tuple[int, int, int], rgb_b: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
        """Blend two RGB tuples using linear interpolation.

        Args:
            rgb_a (tuple[int, int, int]): First RGB tuple.
            rgb_b (tuple[int, int, int]): Second RGB tuple.
            factor (float): Interpolation factor in the 0-1 range.

        Returns:
            tuple[int, int, int]: Resulting blended RGB tuple.
        """
        from ornata.styling.colorkit.spaces import ColorSpaces

        return ColorSpaces.blend(rgb_a, rgb_b, factor)

    @staticmethod
    def mix(spec_a: str, spec_b: str, factor: float) -> str:
        """Blend two colour specifications and return an ANSI sequence.

        Args:
            spec_a (str): First colour specification.
            spec_b (str): Second colour specification.
            factor (float): Interpolation factor in the 0-1 range.

        Returns:
            str: ANSI escape sequence representing the blend.
        """
        from ornata.styling.colorkit.ansi import AnsiConverter
        from ornata.styling.colorkit.palette import PaletteLibrary
        from ornata.styling.colorkit.spaces import ColorSpaces

        rgb_a = Color.resolve_rgb(spec_a)
        rgb_b = Color.resolve_rgb(spec_b)
        if rgb_a is None or rgb_b is None:
            return PaletteLibrary.get_named_color(spec_a if factor < 0.5 else spec_b)
        blended = ColorSpaces.blend(rgb_a, rgb_b, factor)
        return AnsiConverter.rgb_to_ansi(blended)

    @staticmethod
    def rgb_to_ansi(rgb: tuple[int, int, int]) -> str:
        """Return the ANSI escape sequence for ``rgb``.

        Args:
            rgb (tuple[int, int, int]): RGB tuple in 0-255 range.

        Returns:
            str: Foreground ANSI escape sequence.
        """
        from ornata.styling.colorkit.ansi import AnsiConverter

        return AnsiConverter.rgb_to_ansi(rgb)

    @staticmethod
    def rgb_str_to_ansi(rgb_color: str) -> str:
        """Return the ANSI escape sequence for a ``'r,g,b'`` string.

        Args:
            rgb_color (str): Comma-delimited RGB components.

        Returns:
            str: Foreground ANSI escape sequence.
        """
        from ornata.styling.colorkit.ansi import AnsiConverter

        return AnsiConverter.rgb_str_to_ansi(rgb_color)

    @staticmethod
    def hex_to_ansi(hex_color: str) -> str:
        """Return the ANSI escape sequence for ``hex_color``.

        Args:
            hex_color (str): Colour in hexadecimal notation.

        Returns:
            str: Foreground ANSI escape sequence.
        """
        from ornata.styling.colorkit.ansi import AnsiConverter

        return AnsiConverter.hex_to_ansi(hex_color)

    @staticmethod
    def hex_to_bg_ansi(hex_color: str) -> str:
        """Return the background ANSI escape sequence for ``hex_color``.

        Args:
            hex_color (str): Colour in hexadecimal notation.

        Returns:
            str: Background ANSI escape sequence.
        """
        from ornata.styling.colorkit.ansi import AnsiConverter

        return AnsiConverter.hex_to_bg_ansi(hex_color)

    @staticmethod
    def rgb_to_bg_ansi(rgb_color: str) -> str:
        """Return the background ANSI escape sequence for a ``'r,g,b'`` string.

        Args:
            rgb_color (str): Comma-delimited RGB components.

        Returns:
            str: Background ANSI escape sequence.
        """
        from ornata.styling.colorkit.ansi import AnsiConverter

        return AnsiConverter.rgb_str_to_bg_ansi(rgb_color)

    @staticmethod
    def gradient(text: str, start_color: tuple[int, int, int], end_color: tuple[int, int, int]) -> str:
        """Render a gradient across ``text`` using the provided RGB stops.

        Args:
            text (str): Text to decorate.
            start_color (tuple[int, int, int]): Starting RGB tuple.
            end_color (tuple[int, int, int]): Ending RGB tuple.

        Returns:
            str: Text with gradient ANSI escapes applied.
        """

        return resolver.gradient(text, start_color, end_color)

    @staticmethod
    def luminance_from_rgb(r: int, g: int, b: int) -> float:
        """Return the relative luminance for the RGB components.

        Args:
            r (int): Red component.
            g (int): Green component.
            b (int): Blue component.

        Returns:
            float: Relative luminance in the 0-1 range.
        """
        from ornata.styling.colorkit.contrast import ContrastAnalyzer

        return ContrastAnalyzer.relative_luminance((r, g, b))

    @staticmethod
    def contrast_ratio_rgb(rgb_a: tuple[int, int, int], rgb_b: tuple[int, int, int]) -> float:
        """Return the WCAG contrast ratio between ``rgb_a`` and ``rgb_b``.

        Args:
            rgb_a (tuple[int, int, int]): First RGB tuple.
            rgb_b (tuple[int, int, int]): Second RGB tuple.

        Returns:
            float: Contrast ratio where higher is better.
        """
        from ornata.styling.colorkit.contrast import ContrastAnalyzer

        return ContrastAnalyzer.contrast_ratio(rgb_a, rgb_b)

    @staticmethod
    def is_contrast_sufficient(
        fg_spec: ColorSpec,
        bg_spec: ColorSpec = "#000000",
        *,
        large_text: bool = False,
    ) -> bool:
        """Return True when the colour specs satisfy WCAG AA contrast.

        Args:
            fg_spec (ColorSpec): Foreground colour specification.
            bg_spec (ColorSpec): Background colour specification.
            large_text (bool): Whether to use the relaxed AA-large threshold.

        Returns:
            bool: ``True`` when contrast meets the selected threshold.
        """
        from ornata.styling.colorkit.contrast import ContrastAnalyzer

        fg_rgb = Color.resolve_rgb(fg_spec)
        bg_rgb = Color.resolve_rgb(bg_spec)
        if fg_rgb is None or bg_rgb is None:
            return True
        return ContrastAnalyzer.is_aa_compliant(fg_rgb, bg_rgb, large_text=large_text)

    @staticmethod
    def ensure_min_contrast(
        fg_spec: ColorSpec,
        bg_spec: ColorSpec,
        *,
        min_ratio: float = 4.5,
        max_steps: int = 40,
    ) -> str:
        """Return a hex colour adjusted to satisfy ``min_ratio`` contrast.

        Args:
            fg_spec (ColorSpec): Candidate foreground specification.
            bg_spec (ColorSpec): Background specification.
            min_ratio (float): Required minimum contrast ratio.
            max_steps (int): Maximum number of adjustment iterations.

        Returns:
            str: Hexadecimal colour string meeting the requested contrast.
        """
        from ornata.styling.colorkit.contrast import ContrastAnalyzer
        from ornata.styling.colorkit.spaces import ColorSpaces

        fg_rgb = Color.resolve_rgb(fg_spec)
        bg_rgb = Color.resolve_rgb(bg_spec)
        if fg_rgb is None or bg_rgb is None:
            return str(fg_spec)
        adjusted = ContrastAnalyzer.increase_contrast(fg_rgb, bg_rgb, min_ratio=min_ratio, max_steps=max_steps)
        final_ratio = ContrastAnalyzer.contrast_ratio(adjusted, bg_rgb)

        if final_ratio >= min_ratio:
            return ColorSpaces.rgb_to_hex(adjusted)

        # Fallback to black or white whichever meets the ratio (or the best possible)
        candidates = {
            "black": (0, 0, 0),
            "white": (255, 255, 255),
        }
        best_color = adjusted
        best_ratio = final_ratio

        for rgb in candidates.values():
            ratio = ContrastAnalyzer.contrast_ratio(rgb, bg_rgb)
            if ratio >= min_ratio:
                return ColorSpaces.rgb_to_hex(rgb)
            if ratio > best_ratio:
                best_ratio = ratio
                best_color = rgb

        return ColorSpaces.rgb_to_hex(best_color)

    @staticmethod
    def simulate_color_blind(rgb: tuple[int, int, int], mode: str = "protanopia") -> tuple[int, int, int]:
        """Simulate a colour vision deficiency over ``rgb``.

        Args:
            rgb (tuple[int, int, int]): Source RGB tuple.
            mode (str): Simulation mode (protanopia, deuteranopia, tritanopia).

        Returns:
            tuple[int, int, int]: Simulated RGB tuple.
        """
        from ornata.styling.colorkit.vision import ColorVisionSimulator

        return ColorVisionSimulator.simulate(rgb, mode)

    @staticmethod
    def resolve_palette() -> Mapping[str, str]:
        """Return the active named colour palette.

        Returns:
            Mapping[str, str]: Mapping of named tokens to hex values.
        """
        from ornata.styling.colorkit.named_colors import NAMED_COLORS

        return NAMED_COLORS

def resolve_rgb(color_spec: ColorSpec | None) -> tuple[int, int, int] | None:
    """Resolve ``color_spec`` to an RGB tuple.

    Args:
        color_spec (ColorSpec | None): Colour specification or theme token.

    Returns:
        tuple[int, int, int] | None: RGB tuple in 0-255 range when resolved.
    """
    return Color.resolve_rgb(color_spec)

__all__ = ["Color", "resolve_rgb"]
