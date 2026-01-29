"""Colour space conversion helpers for Ornata."""

from __future__ import annotations

import colorsys


class ColorSpaces:
    """Static helpers to move between colour spaces and adjust luminance."""

    @staticmethod
    def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        """Convert an RGB tuple to a #RRGGBB string.

        Args:
            rgb (tuple[int, int, int]): (red, green, blue) components in 0-255 range.

        Returns:
            str: Hexadecimal colour string.
        """

        r, g, b = (ColorSpaces._clamp_component(value) for value in rgb)
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def rgb_to_hsv(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
        """Convert an RGB tuple into HSV (degrees, saturation, value).

        Args:
            rgb (tuple[int, int, int]): RGB components in 0-255 range.

        Returns:
            tuple[float, float, float]: (hue degrees, saturation 0-1, value 0-1).
        """

        r, g, b = (component / 255.0 for component in rgb)
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        return (h * 360.0, s, v)

    @staticmethod
    def hsv_to_rgb(hsv: tuple[float, float, float]) -> tuple[int, ...]:
        """Convert HSV (degrees, saturation, value) to RGB.

        Args:
            hsv (tuple[float, float, float]): (hue degrees, saturation 0-1, value 0-1).

        Returns:
            tuple[int, ...]: RGB tuple in 0-255 range.
        """

        hue, saturation, value = hsv

        r, g, b = colorsys.hsv_to_rgb((hue % 360.0) / 360.0, ColorSpaces._clamp_float(saturation), ColorSpaces._clamp_float(value))
        return ColorSpaces._float_rgb_to_int((r, g, b))

    @staticmethod
    def rgb_to_hsl(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
        """Convert RGB to HSL (degrees, saturation, lightness).

        Args:
            rgb (tuple[int, int, int]): RGB components in 0-255 range.

        Returns:
            tuple[float, float, float]: (hue degrees, saturation 0-1, lightness 0-1).
        """

        r, g, b = (component / 255.0 for component in rgb)
        h, lightness, saturation = colorsys.rgb_to_hls(r, g, b)
        return (h * 360.0, saturation, lightness)

    @staticmethod
    def hsl_to_rgb(hsl: tuple[float, float, float]) -> tuple[int, ...]:
        """Convert HSL (degrees, saturation, lightness) to RGB.

        Args:
            hsl (tuple[float, float, float]): (hue degrees, saturation 0-1, lightness 0-1).

        Returns:
            tuple[int, ...]: RGB tuple in 0-255 range.
        """

        hue, saturation, lightness = hsl

        r, g, b = colorsys.hls_to_rgb((hue % 360.0) / 360.0, ColorSpaces._clamp_float(lightness), ColorSpaces._clamp_float(saturation))
        return ColorSpaces._float_rgb_to_int((r, g, b))

    @staticmethod
    def adjust_luminance(rgb: tuple[int, int, int], amount: float) -> tuple[int, ...]:
        """Lighten or darken an RGB colour by adjusting its lightness.

        Args:
            rgb (tuple[int, int, int]): Source RGB tuple.
            amount (float): Positive for lighter, negative for darker.

        Returns:
            tuple[int, ...]: Adjusted RGB tuple.
        """

        hue, saturation, lightness = ColorSpaces.rgb_to_hsl(rgb)
        lightness = ColorSpaces._clamp_float(lightness + amount)
        return ColorSpaces.hsl_to_rgb((hue, saturation, lightness))

    @staticmethod
    def blend(rgb_a: tuple[int, int, int], rgb_b: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
        """Blend two RGB tuples using a linear interpolation factor.

        Args:
            rgb_a (tuple[int, int, int]): First RGB tuple.
            rgb_b (tuple[int, int, int]): Second RGB tuple.
            factor (float): Interpolation factor in the 0-1 range.

        Returns:
            tuple[int, int, int]: Result of the blend.
        """

        t = ColorSpaces._clamp_float(factor)
        return (
            int(rgb_a[0] + (rgb_b[0] - rgb_a[0]) * t),
            int(rgb_a[1] + (rgb_b[1] - rgb_a[1]) * t),
            int(rgb_a[2] + (rgb_b[2] - rgb_a[2]) * t),
        )

    @staticmethod
    def _float_rgb_to_int(rgb: tuple[float, float, float]) -> tuple[int, ...]:
        """Convert float RGB components in 0-1 range to integers 0-255.

        Args:
            rgb (tuple[float, float, float]): RGB components in 0-1 range.

        Returns:
            tuple[int, ...]: Integer RGB tuple.
        """

        return tuple(int(round(ColorSpaces._clamp_float(component) * 255)) for component in rgb)

    @staticmethod
    def _clamp_component(value: int) -> int:
        """Clamp a colour component to the 0-255 range."""

        return max(0, min(255, int(value)))

    @staticmethod
    def _clamp_float(value: float) -> float:
        """Clamp a float to the 0-1 range."""

        return max(0.0, min(1.0, float(value)))


__all__ = ["ColorSpaces"]
