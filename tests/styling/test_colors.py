from __future__ import annotations

import math

import pytest

from ornata.api.exports.styling import Color, PaletteLibrary
from ornata.definitions.dataclasses.styling import PaletteEntry


@pytest.mark.parametrize(
    "rgb,expected_hex",
    [
        ((12, 34, 56), "#0c2238"),
        ((0, 0, 0), "#000000"),
        ((255, 255, 255), "#ffffff"),
    ],
)
def test_color_rgb_hex_roundtrip(rgb: tuple[int, int, int], expected_hex: str) -> None:
    """rgb_to_hex/hex_to_rgb should round-trip exact values."""

    hex_value = Color.rgb_to_hex(rgb)
    assert hex_value == expected_hex
    assert Color.hex_to_rgb(expected_hex) == rgb
    ansi = Color.rgb_to_ansi(rgb)
    assert ansi.startswith("\u001b[38;2;")
    assert Color.hex_to_ansi(expected_hex).startswith("\u001b[38;2;")


def test_color_space_and_adjustment_helpers() -> None:
    """HSV/HSL conversion helpers should stay numerically stable."""

    rgb = (120, 200, 80)
    hsv = Color.rgb_to_hsv(*rgb)
    assert math.isclose(hsv[0], 100.0, abs_tol=1.0)
    back_to_rgb = Color.hsv_to_rgb(*hsv)
    assert all(abs(original - converted) <= 1 for original, converted in zip(rgb, back_to_rgb))

    hsl = Color.rgb_to_hsl(*rgb)
    rebuilt = Color.hsl_to_rgb(*hsl)
    assert all(abs(original - converted) <= 1 for original, converted in zip(rgb, rebuilt))

    lighter = Color.adjust_luminance(rgb, 0.2)
    assert lighter != rgb
    blended = Color.blend(rgb, (0, 0, 0), 0.5)
    assert blended != rgb


def test_color_gradient_and_mix_utilities() -> None:
    """Gradient and mix helpers should decorate text and honour palette resets."""

    gradient_text = Color.gradient("demo", (255, 0, 0), (0, 0, 255))
    reset = PaletteLibrary.get_effect("reset")
    assert gradient_text.endswith(reset)
    assert "demo" in gradient_text

    mix_result = Color.mix("#ff0000", "#0000ff", 0.25)
    assert mix_result.startswith("\u001b[38;2;")


def test_color_contrast_helpers() -> None:
    """Contrast utilities should report and enforce WCAG requirements."""

    assert Color.is_contrast_sufficient("#000000", "#ffffff")
    assert not Color.is_contrast_sufficient("#777777", "#888888")
    adjusted = Color.ensure_min_contrast("#777777", "#888888", min_ratio=4.5)
    assert Color.is_contrast_sufficient(adjusted, "#888888")


def test_color_register_named_color_updates_palette() -> None:
    """Registering a palette entry should make it resolvable via resolve_rgb."""

    token = "temp_color_token"
    entry = PaletteEntry(token=token, ansi="\u001b[95m", hex_value="#ff00ff")
    Color.register_named_color(entry)
    resolved = Color.resolve_rgb(token)
    assert resolved == (255, 0, 255)
