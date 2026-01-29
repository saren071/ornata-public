"""Tests for ornata.styling.validators."""
from __future__ import annotations

import pytest

from ornata.definitions.dataclasses.styling import ResolvedStyle
from ornata.definitions.enums import BackendTarget
from ornata.definitions.errors import ValidationError
from ornata.styling.validators import StyleValidator, _style_to_dict


def test_style_to_dict_supports_resolved_style() -> None:
    """_style_to_dict should convert ResolvedStyle instances into dictionaries."""
    style = ResolvedStyle(color="#ffffff", opacity=0.9)
    result = _style_to_dict(style)
    assert isinstance(result, dict)
    assert result["color"] == "#ffffff"
    assert pytest.approx(result["opacity"]) == 0.9


def test_validate_property_value_respects_patterns() -> None:
    """Known property patterns must accept good values and reject invalid ones."""
    assert StyleValidator.validate_property_value("opacity", "0.5") is None
    error = StyleValidator.validate_property_value("opacity", "2.0")
    assert error is not None
    assert "Opacity" in error


def test_validate_style_compatibility_reports_invalid_properties() -> None:
    """Style compatibility check should raise errors for unsupported properties."""
    style_dict = {
        "nonexistent-prop": "foo",
        "box-shadow": "0 0 4px red",
        "border-radius": "4px",
    }
    errors = StyleValidator.validate_style_compatibility(style_dict, BackendTarget.CLI)
    assert errors, "Expected validation errors for unsupported properties"
    assert all(isinstance(error, ValidationError) for error in errors)
    joined = " ".join(str(err) for err in errors)
    assert "nonexistent-prop" in joined or "not supported" in joined
    assert "box-shadow" in joined


def test_validate_theme_compatibility_prefixes_component_name() -> None:
    """Theme compatibility errors should include the owning component name."""
    theme_data = {
        "Widget": {"nonexistent-prop": "foo"},
    }
    errors = StyleValidator.validate_theme_compatibility(theme_data, BackendTarget.CLI)
    assert errors
    assert str(errors[0]).startswith("Component 'Widget':")


def test_validate_color_and_numeric_helpers() -> None:
    """Color and numeric helper utilities must enforce formatting constraints."""
    assert StyleValidator.validate_color_value("#112233") is True
    assert StyleValidator.validate_color_value("not-a-color") is False

    assert StyleValidator.validate_numeric_value("10", min_val=0, max_val=20)
    assert StyleValidator.validate_numeric_value("50%", allow_percent=True)
    assert not StyleValidator.validate_numeric_value("-5", min_val=0)
    assert not StyleValidator.validate_numeric_value("abc")
