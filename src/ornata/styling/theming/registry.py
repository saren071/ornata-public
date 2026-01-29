from __future__ import annotations

from ornata.api.exports.definitions import PROPERTIES


class StylingRegistry:
    """Registry of OSTS properties."""

    def __init__(self) -> None:
        pass

    def has_property(self, name: str) -> bool:
        return name in PROPERTIES
