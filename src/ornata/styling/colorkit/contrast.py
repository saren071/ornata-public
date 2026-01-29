"""Contrast and accessibility helpers for Ornata colours."""

from __future__ import annotations


class ContrastAnalyzer:
    """Compute luminance and contrast ratios for RGB colours."""

    @staticmethod
    def relative_luminance(rgb: tuple[int, int, int]) -> float:
        """Return the WCAG relative luminance for ``rgb``."""

        r = rgb[0] / 255.0
        g = rgb[1] / 255.0
        b = rgb[2] / 255.0

        # WCAG sRGB companding: threshold is 0.04045 (not 0.03928)
        def lin(c: float) -> float:
            return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

        r_lin = lin(r)
        g_lin = lin(g)
        b_lin = lin(b)
        return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin

    @staticmethod
    def contrast_ratio(rgb_a: tuple[int, int, int], rgb_b: tuple[int, int, int]) -> float:
        """Return the WCAG contrast ratio between two RGB colours.

        Args:
            rgb_a (tuple[int, int, int]): First RGB tuple.
            rgb_b (tuple[int, int, int]): Second RGB tuple.

        Returns:
            float: Contrast ratio where 1.0 represents no contrast.
        """

        luminance_a = ContrastAnalyzer.relative_luminance(rgb_a)
        luminance_b = ContrastAnalyzer.relative_luminance(rgb_b)
        lighter, darker = (luminance_a, luminance_b) if luminance_a >= luminance_b else (luminance_b, luminance_a)
        return (lighter + 0.05) / (darker + 0.05)

    @staticmethod
    def is_aa_compliant(
        rgb_a: tuple[int, int, int],
        rgb_b: tuple[int, int, int],
        *,
        large_text: bool = False,
    ) -> bool:
        """Return True if the colours meet WCAG AA contrast requirements.

        Args:
            rgb_a (tuple[int, int, int]): Foreground RGB tuple.
            rgb_b (tuple[int, int, int]): Background RGB tuple.
            large_text (bool): Whether AA-large threshold should be used.

        Returns:
            bool: ``True`` when contrast ratio meets the AA guidelines.
        """

        threshold = 3.0 if large_text else 4.5
        return ContrastAnalyzer.contrast_ratio(rgb_a, rgb_b) >= threshold

    @staticmethod
    def increase_contrast(
        rgb: tuple[int, int, int],
        background: tuple[int, int, int],
        *,
        min_ratio: float = 4.5,
        max_steps: int = 40,
    ) -> tuple[int, int, int]:
        """Adjust ``rgb`` until contrast with ``background`` meets ``min_ratio``.

        Args:
            rgb (tuple[int, int, int]): Foreground RGB tuple to adjust.
            background (tuple[int, int, int]): Background RGB tuple.
            min_ratio (float): Minimum acceptable contrast ratio.
            max_steps (int): Number of adjustment attempts.

        Returns:
            tuple[int, int, int]: Adjusted RGB tuple, or the original when the ratio cannot be met.
        """

        current = rgb
        attempt = 0
        while ContrastAnalyzer.contrast_ratio(current, background) < min_ratio and attempt < max_steps:
            from ornata.styling.colorkit.spaces import ColorSpaces
            luminance_fg = ContrastAnalyzer.relative_luminance(current)
            luminance_bg = ContrastAnalyzer.relative_luminance(background)
            delta = -0.04 if luminance_fg > luminance_bg else 0.04
            current = ColorSpaces.adjust_luminance(current, delta)
            attempt += 1
        return current

    @staticmethod
    def _srgb_to_linear(component: float) -> float:
        """Convert an sRGB component into its linear value (kept for API compat)."""
        return component / 12.92 if component <= 0.04045 else ((component + 0.055) / 1.055) ** 2.4


__all__ = ["ContrastAnalyzer"]
