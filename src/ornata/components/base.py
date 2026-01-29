"""Component base classes for declarative UI composition."""

from __future__ import annotations


def _load_layout_style_class() -> type:
    """Import ``LayoutStyle`` lazily to avoid circular imports."""

    from ornata.definitions.dataclasses.layout import LayoutStyle

    return LayoutStyle

__all__ = ["_load_layout_style_class"]
