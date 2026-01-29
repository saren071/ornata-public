"""All Flag(enum) definitions for Ornata."""

from __future__ import annotations

from enum import Flag, auto


class RenderCapability(Flag):
    """Feature capabilities that renderers may support."""
    NONE = 0
    COLOR = auto()
    ALPHA = auto()
    STYLING = auto()
    LAYERS = auto()
    ANIMATION = auto()
    IMAGES = auto()
    VECTORS = auto()
    HARDWARE_ACCEL = auto()
    INTERACTIVE = auto()
    UNICODE = auto()
    EMOJI = auto()
    CUSTOM_FONTS = auto()

__all__ = [
    "RenderCapability"
]