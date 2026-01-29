"""Integration tests for the OSTS parser and style engine."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ornata.api.exports.styling import StyleEngine, diag, parse_stylesheet
from ornata.definitions.dataclasses.styling import Length

if TYPE_CHECKING:
    from pathlib import Path

    from ornata.api.exports.definitions import ResolvedStyle


class _Caps:
    """Terminal capability stub used for style resolution tests."""

    def color_depth(self) -> int:
        """Return the simulated color depth."""
        return 32

    def dpi(self) -> int:
        """Return the simulated DPI."""
        return 96

    def cell_metrics(self) -> tuple[int, int]:
        """Return the simulated cell metrics."""
        return (8, 16)


@pytest.fixture(scope="module")
def osts_text(data_dir: Path) -> str:
    """Load the comprehensive testing stylesheet as raw text."""
    path = data_dir / "styles" / "testing.osts"
    return path.read_text(encoding="utf-8")


@pytest.fixture()
def style_engine(osts_text: str) -> StyleEngine:
    """Provide a StyleEngine seeded with the testing stylesheet."""
    engine = StyleEngine()
    engine.load_stylesheet_text("testing.osts", osts_text)
    return engine


def _resolve_component(
    engine: StyleEngine,
    component_name: str,
    *,
    state: dict[str, bool] | None = None,
) -> ResolvedStyle:
    """Resolve a component style using the shared capability stub."""
    node = type("Node", (), {"component_name": component_name})()
    caps = _Caps()
    return engine.resolve(node=node, state=state or {}, caps=caps)


def test_parse_stylesheet_exposes_all_constructs(osts_text: str) -> None:
    """Parsed stylesheet must include directives, rules, and media blocks."""
    sheet = parse_stylesheet("testing.osts", osts_text)
    assert len(sheet.colors) == 11
    assert set(sheet.colors) >= {"primary", "danger", "success"}
    assert set(sheet.fonts) == {"base", "display"}
    assert set(sheet.keyframes) == {"status-pulse", "rotate"}
    assert len(sheet.media_rules) == 2

    component_names = {rule.component for rule in sheet.rules}
    assert {"TestingContainer", "TestingPanel", "TestingButton"}.issubset(component_names)
    panel_rule = next(rule for rule in sheet.rules if rule.component == "TestingPanel")
    # Default + warn + error blocks
    assert len(panel_rule.blocks) >= 3
    state_sets = {frozenset(block.states) for block in panel_rule.blocks}
    assert frozenset({"warn"}) in state_sets
    assert frozenset({"error"}) in state_sets


def test_style_engine_resolves_state_specific_styles(style_engine: StyleEngine) -> None:
    """State flags must influence the resolved style output."""
    warn_style = _resolve_component(style_engine, "TestingPanel", state={"warn": True})
    assert warn_style.color == "#f9d648"
    assert warn_style.text_decoration is None

    error_style = _resolve_component(style_engine, "TestingPanel", state={"error": True})
    assert error_style.color == "#ff5f56"
    assert error_style.text_decoration == "line-through"


def test_style_engine_handles_interaction_states(style_engine: StyleEngine) -> None:
    """Button state combinations should map to distinct styles."""
    base_button = _resolve_component(style_engine, "TestingButton")
    assert base_button.border is not None
    assert base_button.border.style == "solid"

    hover_button = _resolve_component(style_engine, "TestingButton", state={"hover": True})
    assert hover_button.background == "#ff6f91"
    focus_button = _resolve_component(style_engine, "TestingButton", state={"focus": True})
    assert focus_button.border_color == "#2ecc71"


def test_style_engine_resolves_gradients_and_custom_properties(style_engine: StyleEngine) -> None:
    """GradientCard styles should expose gradient backgrounds and custom props."""

    base = _resolve_component(style_engine, "GradientCard")
    assert base.background_image == "linear-gradient(90deg, primary, accent)"
    assert base.custom_properties is not None
    assert base.custom_properties["--card-border"] == "3px solid"

    focused = _resolve_component(style_engine, "GradientCard", state={"focus": True})
    assert focused.background_image == "linear-gradient(45deg, accent, primary)"


def test_style_engine_maps_font_tokens_to_lengths(style_engine: StyleEngine) -> None:
    """Font tokens should translate into resolved size, spacing, and margins."""

    container = _resolve_component(style_engine, "TestingContainer")
    assert container.font == "base"
    assert isinstance(container.font_size, Length)
    assert container.font_size.value == 15
    assert container.letter_spacing is not None
    assert container.word_spacing is not None
    assert container.margin is not None
    assert container.margin.top.value == 0
    assert container.padding is not None
    assert container.padding.left.value == 2


def test_style_engine_reuses_incremental_component_cache(style_engine: StyleEngine) -> None:
    """Repeated resolutions without states should reuse the cached ResolvedStyle instance."""

    first = _resolve_component(style_engine, "TestingContainer")
    second = _resolve_component(style_engine, "TestingContainer")
    assert first is second


def test_style_engine_tracks_versions(style_engine: StyleEngine, osts_text: str) -> None:
    """Loading and clearing stylesheets should bump the theme version."""

    initial_version = style_engine.theme_version
    style_engine.load_stylesheet_text("testing.osts", osts_text)
    assert style_engine.theme_version == initial_version + 1
    style_engine.clear_styles()
    assert style_engine.theme_version == initial_version + 2


def test_diag_helpers_collect_errors_and_warnings() -> None:
    """Diagnostics module should collect warnings emitted during parsing."""

    noisy_sheet = """
    @unknown { foo: bar; }
    BogusComponent {
        color: primary;
    }
    """

    diag.clear()
    parse_stylesheet("noisy.osts", noisy_sheet)
    warnings = diag.last_warnings()
    assert warnings
    assert "unknown directive" in warnings[0].lower()
    diag.clear()
    diag.warn("warning message")
    diag.error("error message")
    assert diag.last_warnings() == ["warning message"]
    assert diag.last_errors() == ["error message"]
    diag.clear()
    assert diag.last_warnings() == []
    assert diag.last_errors() == []
