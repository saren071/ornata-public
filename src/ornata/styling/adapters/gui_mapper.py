from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.definitions.dataclasses.styling import Length, ResolvedStyle

class GUIMapper:
    """Maps ResolvedStyle to GUI-compatible format with native color support."""

    def __init__(self, resolved: ResolvedStyle):
        """Initialize mapper with resolved style.

        Args:
            resolved: The resolved style to map.
        """
        self.resolved = resolved

    def _length_to_px(self, length: Length | None, *, cell_metrics: Callable[[], tuple[int, int]], font_metrics: Callable[[], tuple[int, int]]) -> int | None:
        if length is None:
            return None
        unit = getattr(length, "unit", "px")
        val = getattr(length, "value", 0)
        if unit == "px":
            return int(val)
        if unit == "cell":
            cm = cell_metrics() if callable(cell_metrics) else None
            cell_w = cm[0] if (isinstance(cm, (tuple, list)) and len(cm) >= 1) else 10
            return int(val * cell_w)
        if unit == "%":
            # Percentage resolution requires layout context; mapper leaves None
            return None
        if unit == "em":
            # Approximate using a default font size when metrics unavailable
            # font_metrics(profile) can be used by higher layer with resolved.font
            base_px = 16
            return int(val * base_px)
        return None

    def _resolve_color_for_gui(self, color_spec: Any) -> str | tuple[int, int, int] | None:
        """Convert color spec to GUI-native format (hex string or RGB tuple).

        Args:
            color_spec: Color specification (string, ColorLiteral, etc.)

        Returns:
            Hex string or RGB tuple for GUI rendering.
        """
        from ornata.definitions.dataclasses.styling import ColorLiteral
        from ornata.styling.colorkit.resolver import ColorResolver

        resolver = ColorResolver()

        if isinstance(color_spec, ColorLiteral):
            return resolver.to_gui(color_spec)

        # For string specs, resolve to ColorLiteral first then convert
        if isinstance(color_spec, str):
            literal = resolver.resolve_literal(color_spec)
            if literal:
                return resolver.to_gui(literal)
            return color_spec  # Fallback to raw string

        return None

    def map_to_gui(self, *, cell_metrics: Callable[[], tuple[int, int]], font_metrics: Callable[[], tuple[int, int]]) -> dict[str, Any]:
        """Map normalized ResolvedStyle into GUI drawing attributes.

        Uses provided capability query functions and preserves colors
        in GUI-native format (hex/RGB) without ANSI conversion.

        Args:
            cell_metrics: Function returning cell dimensions.
            font_metrics: Function returning font metrics.

        Returns:
            Dictionary with GUI-formatted style properties.
        """
        data: dict[str, Any] = {}
        if self.resolved.color:
            data["fg"] = self._resolve_color_for_gui(self.resolved.color)
        if self.resolved.background:
            data["bg"] = self._resolve_color_for_gui(self.resolved.background)
        if self.resolved.border is not None:
            # Border width can be a pixel notion; leave unit conversion to higher level if needed
            data["border_px"] = max(0, int(self.resolved.border.width))
        if self.resolved.border_color:
            data["border_color"] = self._resolve_color_for_gui(self.resolved.border_color)
        if self.resolved.padding is not None:
            t = self._length_to_px(self.resolved.padding.top, cell_metrics=cell_metrics, font_metrics=font_metrics)
            r = self._length_to_px(self.resolved.padding.right, cell_metrics=cell_metrics, font_metrics=font_metrics)
            b = self._length_to_px(self.resolved.padding.bottom, cell_metrics=cell_metrics, font_metrics=font_metrics)
            left_px = self._length_to_px(self.resolved.padding.left, cell_metrics=cell_metrics, font_metrics=font_metrics)
            data["padding_px"] = (t or 0, r or 0, b or 0, left_px or 0)
        if self.resolved.font:
            data["font_profile"] = self.resolved.font
        if self.resolved.font_size is not None:
            data["font_size_px"] = self._length_to_px(self.resolved.font_size, cell_metrics=cell_metrics, font_metrics=font_metrics)
        if self.resolved.outline:
            data["outline"] = self._resolve_color_for_gui(self.resolved.outline)
        if self.resolved.text_decoration_color:
            data["text_decoration_color"] = self._resolve_color_for_gui(self.resolved.text_decoration_color)
        if self.resolved.component_extras:
            data.update(self.resolved.component_extras)
        return data
