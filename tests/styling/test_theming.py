from __future__ import annotations

from pathlib import Path

import pytest

from ornata.api.exports.styling import ThemeManager

SAMPLE_THEME = """
@colors {
    primary: #112233;
    accent: #445566;
}
Component {
    color: primary;
}
"""


@pytest.fixture(scope="module")
def theme_assets_dir(repo_root: Path) -> Path:
    """Return the built-in theme asset directory for ThemeManager tests."""

    return repo_root / "src" / "ornata" / "styling" / "theming" / "assets"


@pytest.fixture()
def theme_manager(theme_assets_dir: Path) -> ThemeManager:
    """Create a ThemeManager bound to the asset directory for isolation."""

    return ThemeManager(theme_dir=theme_assets_dir)


def test_theme_manager_resolve_token_and_version(theme_manager: ThemeManager) -> None:
    """Registering and activating themes should bump the version and resolve tokens."""

    invalidations = 0

    def _invalidate() -> None:
        nonlocal invalidations
        invalidations += 1

    theme_manager.register_cache_invalidator(_invalidate)
    previous_version = theme_manager.version
    theme_manager.load_theme_text("unit_theme", SAMPLE_THEME, activate=True)

    assert theme_manager.get_active_theme() is not None
    assert theme_manager.version > previous_version
    assert invalidations >= 1
    assert theme_manager.resolve_token("primary") == "#112233"
    assert theme_manager.resolve_token("red")  # falls back to named palette


def test_theme_manager_extend_and_palette(theme_manager: ThemeManager) -> None:
    """Extending a registered theme should merge overrides into the new palette."""

    theme_manager.load_theme_text("base_theme", SAMPLE_THEME, activate=True)
    derived = theme_manager.extend_theme("base_theme", {"accent": "#abcdef"}, name="base_override")

    assert derived.palette["accent"] == "#abcdef"
    assert theme_manager.palette_for("base_override") == derived.palette


def test_theme_manager_load_theme_file_and_activation(theme_assets_dir: Path) -> None:
    """Themes loaded from disk should be selectable and validated."""

    manager = ThemeManager(theme_dir=theme_assets_dir)
    path = theme_assets_dir / "light.osts"
    theme = manager.load_theme_file(path, activate=False)
    manager.set_active_theme(theme.name)

    assert manager.get_active_theme() is not None
    assert theme.name in manager.list_themes()

    with pytest.raises(ValueError):
        manager.set_active_theme("missing-theme")
