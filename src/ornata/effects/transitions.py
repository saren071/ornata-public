"""Declarative style transitions for text using Ornata's rendering pipeline.

Provides a Transition API to animate between two color specs or gradients.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def ease_in_out(t: float) -> float:
    # smoothstep-like
    return t * t * (3 - 2 * t)


class Transition:
    _lerp = staticmethod(_lerp)
    @staticmethod
    def color_fade(
        text: str,
        start: str,
        end: str,
        duration: float = 1.0,
        fps: int = 30,
        easing: Callable[[float], float] | None = None,
    ) -> None:
        """Animate text color from start spec to end spec over duration."""
        # TODO: Implement.
        pass

    @staticmethod
    def blink(text: str, color: str = "fg", cycles: int = 3, fps: int = 6) -> None:
        # TODO: Implement.
        pass
