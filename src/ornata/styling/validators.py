"""
Style validation utilities for Ornata.

This module provides comprehensive validation for style compatibility across different renderers,
style property validation, and theme validation.
"""

from __future__ import annotations

from dataclasses import fields as _dc_fields
from dataclasses import is_dataclass
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger
from ornata.definitions.enums import BackendTarget, RendererType

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ornata.definitions.dataclasses.styling import ResolvedStyle
    from ornata.definitions.errors import ValidationError

def _style_to_dict(style_obj: ResolvedStyle | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(style_obj, dict):
        return style_obj
    if is_dataclass(style_obj):
        return {f.name: getattr(style_obj, f.name) for f in _dc_fields(style_obj)}
    try:
        return dict(style_obj)
    except Exception:
        return {}


class StyleValidator:
    """Validates style compatibility and correctness across renderers."""
    logger = get_logger(__name__)

    # Property value patterns for validation

    @staticmethod
    def validate_style_compatibility(style: ResolvedStyle | Mapping[str, Any], backend_target: BackendTarget) -> list[ValidationError]:
        """
        Validate that a resolved style is compatible with the specified backend target.

        Args:
            style: The resolved style to validate
            backend_target: The target backend target

        Returns:
            List of validation errors found
        """
        from ornata.definitions.constants import VALID_STYLING_PROPERTIES
        errors: list[ValidationError] = []
        style_dict = _style_to_dict(style)
        # Map BackendTarget to RendererType for validation
        renderer_type = StyleValidator._renderer_type_for_backend(backend_target)
        valid_properties = VALID_STYLING_PROPERTIES.get(renderer_type, set())

        # property compatibility
        for prop_name in style_dict.keys():
            if prop_name not in valid_properties:
                StyleValidator.logger.warning(f"Property '{prop_name}' is not supported by {backend_target.value} backend")
                from ornata.definitions.errors import ValidationError
                errors.append(ValidationError(f"Property '{prop_name}' is not supported by {backend_target.value} backend"))

        # value validation
        for prop_name, prop_value in style_dict.items():
            error = StyleValidator._validate_property_value(prop_name, str(prop_value))
            if error:
                StyleValidator.logger.warning(f"Style validation error: {error}")
                from ornata.definitions.errors import ValidationError
                errors.append(ValidationError(error))

        # renderer-specific
        if backend_target == BackendTarget.CLI:
            errors.extend(StyleValidator._validate_cli_specific(style_dict))
        elif backend_target == BackendTarget.GUI:
            errors.extend(StyleValidator._validate_gui_specific(style_dict))

        if errors:
            StyleValidator.logger.warning(f"Found {len(errors)} style validation errors for {backend_target.value} backend")
        return errors

    @staticmethod
    def _renderer_type_for_backend(backend_target: BackendTarget) -> RendererType:
        """Resolve the renderer type used for ``backend_target``."""

        if backend_target is BackendTarget.GUI:
            return RendererType.DIRECTX11
        if backend_target is BackendTarget.TTY:
            return RendererType.CPU
        if backend_target is BackendTarget.CLI:
            return RendererType.CPU
        return RendererType.CPU

    @staticmethod
    def validate_property_value(property_name: str, value: str) -> str | None:
        """
        Validate a single property value.

        Args:
            property_name: The CSS property name
            value: The property value to validate

        Returns:
            Error message if invalid, None if valid
        """
        return StyleValidator._validate_property_value(property_name, value)

    @staticmethod
    def _validate_property_value(property_name: str, value: str) -> str | None:
        """Internal property value validation."""
        from ornata.definitions.constants import VALUE_PATTERNS
        if property_name not in VALUE_PATTERNS:
            # Unknown property - allow for extensibility
            return None

        pattern = VALUE_PATTERNS[property_name]
        if not pattern.match(str(value)):
            return f"Invalid value '{value}' for property '{property_name}'"

        # Additional numeric validations
        if property_name in ("opacity",):
            try:
                num_val = float(value)
                if not (0.0 <= num_val <= 1.0):
                    return f"Opacity must be between 0.0 and 1.0, got {num_val}"
            except ValueError:
                return f"Opacity must be a number, got '{value}'"

        elif property_name == "z-index":
            try:
                int(value)
            except ValueError:
                return f"Z-index must be an integer, got '{value}'"

        return None

    @staticmethod
    def _validate_cli_specific(style: dict[str, Any]) -> list[ValidationError]:
        """CLI-specific style validations."""
        errors: list[ValidationError] = []
        unsupported_props = {"box-shadow", "text-shadow", "transform", "transition", "animation"}
        for prop in unsupported_props:
            if prop in style:
                from ornata.definitions.errors import ValidationError
                errors.append(ValidationError(f"CLI renderer does not support '{prop}' property"))
        if "border-radius" in style and style["border-radius"] not in (None, "0", 0):
            from ornata.definitions.errors import ValidationError
            errors.append(ValidationError("CLI renderer does not support border-radius"))
        return errors

    @staticmethod
    def _validate_gui_specific(style: dict[str, Any]) -> list[ValidationError]:
        return []

    @staticmethod
    def validate_theme_compatibility(theme_data: dict[str, dict[str, str]], backend_target: BackendTarget) -> list[ValidationError]:
        """
        Validate that a theme is compatible with the specified renderer.

        Args:
            theme_data: Theme dictionary with component styles
            renderer_type: Target renderer type

        Returns:
            List of validation errors found
        """
        errors: list[ValidationError] = []

        for component_name, component_styles in theme_data.items():
            # Validate each component's styles
            component_errors = StyleValidator.validate_style_compatibility(component_styles, backend_target)
            for error in component_errors:
                # Prefix component name to error message
                from ornata.definitions.errors import ValidationError
                new_error = ValidationError(f"Component '{component_name}': {error}")
                errors.append(new_error)

        return errors

    @staticmethod
    def validate_color_value(color_value: str) -> bool:
        """
        Validate that a color value is properly formatted.

        Args:
            color_value: Color value to validate

        Returns:
            True if valid, False otherwise
        """
        from ornata.definitions.constants import VALUE_PATTERNS
        from ornata.styling.colorkit.named_colors import NAMED_COLORS

        token = color_value.strip()
        if not token:
            return False

        if VALUE_PATTERNS["color"].fullmatch(token) is None:
            return False
        if token.isalpha():
            allowed_names = {
                *{name.lower() for name in NAMED_COLORS},
                "transparent",
            }
            return token.lower() in allowed_names
        return True

    @staticmethod
    def validate_numeric_value(value: str, min_val: float | None = None, max_val: float | None = None, allow_percent: bool = False) -> bool:
        """
        Validate a numeric CSS value.

        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            allow_percent: Whether to allow percentage values

        Returns:
            True if valid, False otherwise
        """
        try:
            if allow_percent and value.endswith("%"):
                num_val = float(value[:-1])
            else:
                num_val = float(value)

            if min_val is not None and num_val < min_val:
                return False
            if max_val is not None and num_val > max_val:
                return False

            return True
        except ValueError:
            return False


__all__ = ["StyleValidator"]
