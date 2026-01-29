"""Ornata Styling public API exports.

This package hosts the styling language and resolution engine used across
all renderers (CLI/TTY/GUI/GPU). It is backend-agnostic
and also contains Style tokens and theming hooks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.styling.runtime.runtime import get_styling_runtime

if TYPE_CHECKING:
    from ornata.styling.language.engine import StyleEngine


def get_style_engine() -> StyleEngine:
    """Return the process-global :class:`StyleEngine`.

    Returns:
        StyleEngine: Shared style engine instance.
    """

    return get_styling_runtime().get_engine()


__all__ = [
    "get_style_engine",
]
