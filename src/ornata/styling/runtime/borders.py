"""Border symbol sets and styles for different capabilities."""

from __future__ import annotations


class StylingBorders:
    """Border symbol sets and styles for different capabilities."""

    def __init__(self):
        pass


    def border_set(self, style: str = "solid") -> str:
        """Get border character set for a given style."""
        # TODO: switch to using unicode
        return style


    def get_border_chars(self, style: str = "solid") -> str:
        """Alias for border_set for backward compatibility."""
        # TODO: Deprecate as there should be NO backward compatibility
        return self.border_set(style)


    __all__ = [
        "border_set",
        "get_border_chars",
    ]
