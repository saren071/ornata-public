from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.definitions.dataclasses.styling import Length, ResolvedStyle

class GUIMapper:
    def __init__(self, resolved: ResolvedStyle):
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

    def map_to_gui(self, *, cell_metrics: Callable[[], tuple[int, int]], font_metrics: Callable[[], tuple[int, int]]) -> dict[str, Any]:
        """Map normalized ResolvedStyle into GUI drawing attributes.

        Uses provided capability query functions.
        """
        data: dict[str, Any] = {}
        if self.resolved.color:
            data["fg"] = self.resolved.color
        if self.resolved.background:
            data["bg"] = self.resolved.background
        if self.resolved.border is not None:
            # Border width can be a pixel notion; leave unit conversion to higher level if needed
            data["border_px"] = max(0, int(self.resolved.border.width))
        if self.resolved.border_color:
            data["border_color"] = self.resolved.border_color
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
            data["outline"] = self.resolved.outline
        if self.resolved.component_extras:
            data.update(self.resolved.component_extras)
        return data
