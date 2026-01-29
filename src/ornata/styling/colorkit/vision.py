"""Colour vision deficiency simulation utilities."""

from __future__ import annotations


class ColorVisionSimulator:
    """Transform RGB colours to approximate common colour vision deficiencies."""

    @staticmethod
    def simulate(rgb: tuple[int, int, int], mode: str = "protanopia") -> tuple[int, int, int]:
        """Return an RGB tuple transformed for a colour vision deficiency.

        Args:
            rgb (tuple[int, int, int]): Source RGB tuple.
            mode (str): Simulation mode (protanopia, deuteranopia, tritanopia).

        Returns:
            tuple[int, int, int]: Simulated RGB tuple.
        """
        from ornata.definitions.constants import TRANSFORMS

        transform = TRANSFORMS.get(mode.lower(), TRANSFORMS["protanopia"])
        r, g, b = [component / 255.0 for component in rgb]
        r2 = r * transform[0][0] + g * transform[0][1] + b * transform[0][2]
        g2 = r * transform[1][0] + g * transform[1][1] + b * transform[1][2]
        b2 = r * transform[2][0] + g * transform[2][1] + b * transform[2][2]
        return (
            int(max(0.0, min(1.0, r2)) * 255),
            int(max(0.0, min(1.0, g2)) * 255),
            int(max(0.0, min(1.0, b2)) * 255),
        )


__all__ = ["ColorVisionSimulator"]
