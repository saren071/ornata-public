"""Gradient rendering helpers."""

from __future__ import annotations


class GradientRenderer:
    """Render linear gradients for ANSI capable consoles."""

    _MIN_STEPS = 1

    @staticmethod
    def render_gradient(text: str, start_color: tuple[int, int, int], end_color: tuple[int, int, int]) -> str:
        """Apply a linear gradient across ``text``."""
        if not text:
            return ""

        n = len(text)
        if n == 1:
            r, g, b = start_color
            return f"\033[38;2;{int(r)};{int(g)};{int(b)}m{text}"

        steps = max(n - 1, GradientRenderer._MIN_STEPS)
        inv = 1.0 / steps if steps else 0.0
        r0, g0, b0 = start_color
        dr = end_color[0] - r0
        dg = end_color[1] - g0
        db = end_color[2] - b0

        parts: list[str] = []
        ap = parts.append
        for i, ch in enumerate(text):
            t = i * inv
            r = int(r0 + dr * t)
            g = int(g0 + dg * t)
            b = int(b0 + db * t)
            ap(f"\033[38;2;{r};{g};{b}m{ch}")
        return "".join(parts)

render_gradient = GradientRenderer.render_gradient

__all__ = ["GradientRenderer", "render_gradient"]
