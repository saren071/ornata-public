"""Shared layout utilities for spacing, alignment, and box model helpers."""

from __future__ import annotations

from typing import Literal

JustifyContent = Literal["start", "center", "end", "space-between", "space-around", "space-evenly"]

__all__ = [
    "clamp_int",
    "compute_justify_spacing",
    "align_text",
]


def clamp_int(value: int, minimum: int | None, maximum: int | None) -> int:
    if minimum is not None:
        value = max(value, minimum)
    if maximum is not None:
        value = min(value, maximum)
    return value


def compute_justify_spacing(
    count: int,
    base_gap: int,
    remaining: int,
    justify: JustifyContent,
) -> tuple[int, int]:
    """Return (offset, gap) according to justification and remaining space."""
    offset = 0
    gap = base_gap
    if count <= 0:
        return offset, gap
    if justify == "center":
        offset = remaining // 2
    elif justify == "end":
        offset = remaining
    elif justify == "space-between" and count > 1:
        gap = base_gap + (remaining // (count - 1))
    elif justify == "space-around":
        gap = base_gap + (remaining // count)
        offset = gap // 2
    elif justify == "space-evenly":
        gap = base_gap + (remaining // (count + 1))
        offset = gap
    return offset, gap


def align_text(
    text: str,
    width: int,
    mode: str = "left",
) -> str:
    """Pad a rendered text segment to `width` according to alignment mode.

    Assumes `text` is already markup-rendered; uses visible_width to compute
    grapheme-aware length.
    """
    # Simple length check for now as markup was removed
    visible_length = len(text)
    padding_space = max(0, width - visible_length)
    if mode in ("center", "centre"):
        left_padding = padding_space // 2
        right_padding = padding_space - left_padding
        return (" " * left_padding) + text + (" " * right_padding)
    if mode in ("right", "end"):
        return (" " * padding_space) + text
    return text + (" " * padding_space)
