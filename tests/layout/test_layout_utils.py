"""Unit coverage for layout utility helpers."""

from __future__ import annotations

from ornata.api.exports.layout import align_text, clamp_int, compute_justify_spacing


def test_clamp_int_enforces_bounds() -> None:
    """Values should be clamped to the provided limits."""

    assert clamp_int(5, 10, 20) == 10
    assert clamp_int(25, 10, 20) == 20
    assert clamp_int(15, 10, 20) == 15


def test_compute_justify_spacing_variants() -> None:
    """Remaining space should be distributed according to policy."""

    offset, gap = compute_justify_spacing(3, 1, 6, "space-between")
    assert offset == 0
    assert gap == 4  # base gap + distributed remainder

    offset, gap = compute_justify_spacing(3, 1, 6, "space-around")
    assert offset == gap // 2
    assert gap >= 3

    offset, gap = compute_justify_spacing(2, 1, 6, "space-evenly")
    assert offset == gap
    assert gap >= 3

    offset, gap = compute_justify_spacing(2, 1, 6, "center")
    assert offset == 3
    assert gap == 1

    offset, gap = compute_justify_spacing(2, 1, 6, "end")
    assert offset == 6
    assert gap == 1


def test_align_text_modes() -> None:
    """Text alignment should pad according to the requested mode."""

    assert align_text("hi", 6, mode="center") == "  hi  "
    assert align_text("hi", 6, mode="right") == "    hi"
    assert align_text("hi", 6) == "hi    "
