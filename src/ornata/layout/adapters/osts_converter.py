"""OSTS to layout style conversion utilities. OSTS is Ornata Style & Theming Sheet."""

from __future__ import annotations

import logging
from threading import RLock
from typing import TYPE_CHECKING, Any

from ornata.definitions.enums import BackendTarget
from ornata.layout.engine.engine import LayoutStyle

if TYPE_CHECKING:
    from ornata.definitions.dataclasses.styling import ResolvedStyle

logger = logging.getLogger(__name__)


class OSTSLayoutConverter:
    """Converts OSTS resolved style objects to layout styles."""

    def __init__(self) -> None:
        """Initialize the OSTS layout converter."""
        self._lock = RLock()

    def convert_osts_to_layout_style(self, resolved_style: ResolvedStyle, backend_target: BackendTarget = BackendTarget.GUI) -> LayoutStyle:
        """Convert a resolved OSTS style to a LayoutStyle.

        Args:
            resolved_style: Fully resolved OSTS style object.
            backend_target: Target backend type for unit conversions.

        Returns:
            Converted LayoutStyle object.
        """
        with self._lock:
            layout_style = LayoutStyle()

            # Map known properties from the resolved style to layout properties
            property_map: dict[str, Any] = {
                "width": getattr(resolved_style, "width", None),
                "height": getattr(resolved_style, "height", None),
                "min-width": getattr(resolved_style, "min_width", None),
                "min-height": getattr(resolved_style, "min_height", None),
                "max-width": getattr(resolved_style, "max_width", None),
                "max-height": getattr(resolved_style, "max_height", None),
                "flex-grow": getattr(resolved_style, "flex_grow", None),
                "flex-shrink": getattr(resolved_style, "flex_shrink", None),
                "flex-basis": getattr(resolved_style, "flex_basis", None),
                "margin": getattr(resolved_style, "margin", None),
                "padding": getattr(resolved_style, "padding", None),
                "direction": getattr(resolved_style, "flex_direction", None) or getattr(resolved_style, "direction", None),
                "wrap": getattr(resolved_style, "flex_wrap", None) or getattr(resolved_style, "wrap", None),
                "gap": getattr(resolved_style, "gap", None),
                "justify": getattr(resolved_style, "justify_content", None),
                "align": getattr(resolved_style, "align_items", None),
                "display": getattr(resolved_style, "display", None),
                "position": getattr(resolved_style, "position", None),
                "top": getattr(resolved_style, "top", None),
                "right": getattr(resolved_style, "right", None),
                "bottom": getattr(resolved_style, "bottom", None),
                "left": getattr(resolved_style, "left", None),
                # Grid
                "grid-template-columns": getattr(resolved_style, "grid_template_columns", None),
                "grid-template-rows": getattr(resolved_style, "grid_template_rows", None),
                "grid-column-gap": getattr(resolved_style, "grid_column_gap", None),
                "grid-row-gap": getattr(resolved_style, "grid_row_gap", None),
                # Margin/padding sides
                "margin-top": getattr(resolved_style, "margin_top", None),
                "margin-right": getattr(resolved_style, "margin_right", None),
                "margin-bottom": getattr(resolved_style, "margin_bottom", None),
                "margin-left": getattr(resolved_style, "margin_left", None),
                "padding-top": getattr(resolved_style, "padding_top", None),
                "padding-right": getattr(resolved_style, "padding_right", None),
                "padding-bottom": getattr(resolved_style, "padding_bottom", None),
                "padding-left": getattr(resolved_style, "padding_left", None),
                # Overflow
                "overflow": getattr(resolved_style, "overflow", None),
                "overflow-x": getattr(resolved_style, "overflow_x", None),
                "overflow-y": getattr(resolved_style, "overflow_y", None),
            }

            for prop_name, prop_value in property_map.items():
                if prop_value is None:
                    continue
                try:
                    self._convert_property(prop_name, prop_value, layout_style, backend_target)
                except Exception as e:
                    logger.warning(f"Failed to convert OSTS property '{prop_name}': {e}")

            return layout_style

    def _convert_property(self, prop_name: str, prop_value: Any, layout_style: LayoutStyle, backend_target: BackendTarget) -> None:
        """Convert a single OSTS property to layout style.

        Args:
            prop_name: Property name.
            prop_value: Property value.
            layout_style: LayoutStyle to modify.
            backend_target: Target backend type for unit conversions.
        """
        # Handle different property types with renderer-specific conversions
        if prop_name == "width":
            layout_style.width = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "height":
            layout_style.height = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "min-width":
            layout_style.min_width = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "min-height":
            layout_style.min_height = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "max-width":
            layout_style.max_width = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "max-height":
            layout_style.max_height = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "flex-grow":
            layout_style.flex_grow = self._parse_number(prop_value)
        elif prop_name == "flex-shrink":
            layout_style.flex_shrink = self._parse_number(prop_value)
        elif prop_name == "flex-basis":
            layout_style.flex_basis = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "margin":
            layout_style.margin = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "padding":
            layout_style.padding = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "direction":
            layout_style.direction = self._parse_direction(prop_value)
        elif prop_name == "wrap":
            layout_style.wrap = self._parse_boolean(prop_value)
        elif prop_name == "gap":
            layout_style.gap = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "justify":
            layout_style.justify = self._parse_justify(prop_value)
        elif prop_name == "align":
            layout_style.align = self._parse_align(prop_value)
        elif prop_name == "display":
            layout_style.display = self._parse_display(prop_value)
        elif prop_name == "position":
            layout_style.position = self._parse_position(prop_value)
        elif prop_name == "top":
            layout_style.top = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "right":
            layout_style.right = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "bottom":
            layout_style.bottom = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "left":
            layout_style.left = self._parse_dimension(prop_value, backend_target)
        # Grid properties
        elif prop_name == "grid-template-columns":
            layout_style.grid_template_columns = str(prop_value)
        elif prop_name == "grid-template-rows":
            layout_style.grid_template_rows = str(prop_value)
        elif prop_name == "grid-column-gap":
            layout_style.grid_column_gap = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "grid-row-gap":
            layout_style.grid_row_gap = self._parse_dimension(prop_value, backend_target)
        # Margin/padding sides
        elif prop_name == "margin-top":
            layout_style.margin_top = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "margin-right":
            layout_style.margin_right = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "margin-bottom":
            layout_style.margin_bottom = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "margin-left":
            layout_style.margin_left = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "padding-top":
            layout_style.padding_top = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "padding-right":
            layout_style.padding_right = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "padding-bottom":
            layout_style.padding_bottom = self._parse_dimension(prop_value, backend_target)
        elif prop_name == "padding-left":
            layout_style.padding_left = self._parse_dimension(prop_value, backend_target)
        # Overflow properties
        elif prop_name == "overflow":
            layout_style.overflow = self._parse_overflow(prop_value)
        elif prop_name == "overflow-x":
            layout_style.overflow_x = self._parse_overflow(prop_value)
        elif prop_name == "overflow-y":
            layout_style.overflow_y = self._parse_overflow(prop_value)
        else:
            # Unknown property - log and ignore
            logger.debug(f"Ignoring unknown layout property: {prop_name}")

    def _parse_dimension(self, value: Any, backend_target: BackendTarget) -> int:
        """Parse dimension value (px, etc.) with renderer-specific conversions.

        Args:
            value: OSTS value to parse.
            backend_target: Target backend type for unit conversions.

        Returns:
            Parsed dimension as integer, or None.
        """
        if isinstance(value, str):
            value_str = value.strip()
            if value_str.endswith("px"):
                try:
                    px_value = int(value_str[:-2])
                    # Convert pixels to renderer units
                    if backend_target == BackendTarget.CLI:
                        # CLI uses cells, assume 8px per cell width, 16px per cell height
                        return px_value  # Keep as pixels for now, renderer handles conversion
                    elif backend_target == BackendTarget.TTY:
                        return px_value  # TTY also uses pixels
                    else:
                        return px_value
                except ValueError:
                    pass
            elif value_str.endswith("cell"):
                try:
                    cell_value = int(value_str[:-4])
                    # Convert cells to pixels for non-cell-based renderers
                    if backend_target == BackendTarget.GUI:
                        # Assume 8px per cell width, 16px per cell height
                        return cell_value * 8  # Conservative estimate
                    else:
                        return cell_value
                except ValueError:
                    pass
            elif value_str.isdigit():
                try:
                    return int(value_str)
                except ValueError:
                    pass
        elif isinstance(value, int):
            return value
        return 0

    def _parse_number(self, value: Any) -> float:
        """Parse numeric value.

        Args:
            value: OSTS value to parse.

        Returns:
            Parsed number as float.
        """
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return 0.0
        return 0.0

    def _parse_direction(self, value: Any):
        """Parse flex direction.

        Args:
            value: OSTS value to parse.

        Returns:
            Direction string.
        """
        if isinstance(value, str):
            if value in ("row", "column"):
                return value
        return "row"

    def _parse_boolean(self, value: Any) -> bool:
        """Parse boolean value.

        Args:
            value: OSTS value to parse.

        Returns:
            Parsed boolean.
        """
        if isinstance(value, str):
            return value.lower() in ("true", "1", "yes", "on")
        return False

    def _parse_justify(self, value: Any):
        """Parse justify-content value.

        Args:
            value: OSTS value to parse.

        Returns:
            Justify string.
        """
        if isinstance(value, str):
            valid_values = ("start", "center", "end", "space-between", "space-around", "space-evenly")
            if value in valid_values:
                return value
        return "start"

    def _parse_align(self, value: Any):
        """Parse align-items value.

        Args:
            value: OSTS value to parse.

        Returns:
            Align string.
        """
        if isinstance(value, str):
            valid_values = ("start", "center", "end", "stretch")
            if value in valid_values:
                return value
        return "stretch"

    def _parse_display(self, value: Any) -> str:
        """Parse display value.

        Args:
            value: OSTS value to parse.

        Returns:
            Display string.
        """
        if isinstance(value, str):
            valid_values = ("block", "none", "flex", "grid")
            if value in valid_values:
                return value
        return "block"

    def _parse_position(self, value: Any) -> str:
        """Parse position value.

        Args:
            value: OSTS value to parse.

        Returns:
            Position string.
        """
        if isinstance(value, str):
            valid_values = ("static", "relative", "absolute", "fixed")
            if value in valid_values:
                return value
        return "static"

    def _parse_overflow(self, value: Any) -> str:
        """Parse overflow value.

        Args:
            value: OSTS value to parse.

        Returns:
            Overflow string.
        """
        if isinstance(value, str):
            valid_values = ("visible", "hidden", "scroll", "auto")
            if value in valid_values:
                return value
        return "visible"


# Global converter instance
_osts_converter: OSTSLayoutConverter | None = None


def get_osts_converter() -> OSTSLayoutConverter:
    """Get the global OSTs layout converter instance.

    Returns:
        The global OSTs layout converter.
    """
    global _osts_converter
    if _osts_converter is None:
        _osts_converter = OSTSLayoutConverter()
    return _osts_converter


def osts_to_layout_style(resolved_style: ResolvedStyle, backend_target: BackendTarget = BackendTarget.GUI) -> LayoutStyle:
    """Convert a resolved OSTS style to LayoutStyle.

    Args:
        resolved_style: Fully resolved OSTS style object.
        backend_target: Target backend type for unit conversions.

    Returns:
        Converted LayoutStyle.
    """
    converter = get_osts_converter()
    return converter.convert_osts_to_layout_style(resolved_style, backend_target)
    