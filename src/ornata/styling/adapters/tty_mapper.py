from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.definitions.dataclasses.styling import Length, ResolvedStyle

class TTYMapper:
    def __init__(self, resolved: ResolvedStyle):
        self.resolved = resolved
    
    def _hex_to_rgb(self, value: str) -> tuple[int, int, int] | None:
        s = value.strip().lower()
        if s.startswith("#") and len(s) == 7:
            try:
                r = int(s[1:3], 16)
                g = int(s[3:5], 16)
                b = int(s[5:7], 16)
                return r, g, b
            except Exception:
                return None
        if s.startswith("rgb(") and s.endswith(")"):
            try:
                parts = s[4:-1].split(",")
                r = int(parts[0])
                g = int(parts[1])
                b = int(parts[2])
                return r, g, b
            except Exception:
                return None
        return None

    def _rgb_to_ansi256(self, r: int, g: int, b: int) -> int:
        # Map to grayscale if near gray
        if r == g == b:
            if r < 8:
                return 16
            if r > 248:
                return 231
            return 232 + int((r - 8) / 10.8)
        # 6x6x6 color cube

        def _to_6(x: int) -> int:
            return int(round(x / 255 * 5))

        ri, gi, bi = _to_6(r), _to_6(g), _to_6(b)
        return 16 + 36 * ri + 6 * gi + bi

    def _rgb_to_ansi16(self, r: int, g: int, b: int) -> int:
        # Approximate mapping to 16-color ANSI using luminance and primary channels
        # Base colors 0-7 and bright 8-15
        bright = (r + g + b) / 3 > 127
        idx = 0
        if r > 127:
            idx |= 1
        if g > 127:
            idx |= 2
        if b > 127:
            idx |= 4
        return (8 if bright else 0) + (idx if idx != 0 else 0)

    def _downsample_color(self, color: str, depth: str) -> dict[str, Any]:
        rgb = self._hex_to_rgb(color)
        if rgb is None:
            return {"hex": color}
        r, g, b = rgb
        d = (depth or "C256").upper()
        if d == "TRUECOLOR":
            return {"hex": f"#{r:02x}{g:02x}{b:02x}"}
        if d in ("C256", "256"):
            return {"ansi256": self._rgb_to_ansi256(r, g, b)}
        if d in ("C16", "16"):
            return {"ansi16": self._rgb_to_ansi16(r, g, b)}
        return {"hex": f"#{r:02x}{g:02x}{b:02x}"}

    def _length_to_cells(self, length: Length | None) -> int:
        """Returns integer cell count; '%': 0 (layout-dependent), 'px': caller converts via pixel_to_cell"""
        if length is None:
            return 0
        unit = getattr(length, "unit", "px")
        val = getattr(length, "value", 0)
        if unit == "cell":
            return int(val)
        if unit == "px":
            # caller handles px→cell via pixel_to_cell
            return int(val)
        if unit == "%":
            # layout-dependent; not resolved here
            return 0
        if unit == "em":
            # approximate: 1em ~ 1 cell
            return int(val)
        return 0

    def map_to_tty(self, *, pixel_to_cell: Callable[[float | int], int], color_depth: Callable[[], str]) -> dict[str, Any]:
        """Map normalized ResolvedStyle into TTY-friendly attributes.

        Returns a small dict used by the CLI/TTY adapter to render borders, padding, colors.
        Includes best-effort downsampling based on color depth.
        """
        data: dict[str, Any] = {}
        _depth_raw = color_depth() if callable(color_depth) else color_depth
        depth: str = str(_depth_raw or "C256")
        if self.resolved.color:
            data["fg"] = self._downsample_color(str(self.resolved.color), depth)
        if self.resolved.background:
            data["bg"] = self._downsample_color(str(self.resolved.background), depth)
        if self.resolved.border is not None:
            width_cells = max(0, int(pixel_to_cell(self.resolved.border.width)))
            # Enforce minimum of 1 cell when a non-zero border resolves to 0 cells
            if self.resolved.border.width > 0 and width_cells == 0:
                width_cells = 1
            data["border_width"] = max(0, width_cells)
        if self.resolved.border_color:
            data["border_color"] = self._downsample_color(str(self.resolved.border_color), depth)
        if self.resolved.padding is not None:
            t = self._length_to_cells(self.resolved.padding.top)
            r = self._length_to_cells(self.resolved.padding.right)
            b = self._length_to_cells(self.resolved.padding.bottom)
            left_cells = self._length_to_cells(self.resolved.padding.left)
            # Convert px→cell if necessary for any px units (best-effort)
            t = t if getattr(self.resolved.padding.top, "unit", "cell") == "cell" else pixel_to_cell(getattr(self.resolved.padding.top, "value", 0))
            r = r if getattr(self.resolved.padding.right, "unit", "cell") == "cell" else pixel_to_cell(getattr(self.resolved.padding.right, "value", 0))
            b = b if getattr(self.resolved.padding.bottom, "unit", "cell") == "cell" else pixel_to_cell(getattr(self.resolved.padding.bottom, "value", 0))
            left_cells = left_cells if getattr(self.resolved.padding.left, "unit", "cell") == "cell" else pixel_to_cell(getattr(self.resolved.padding.left, "value", 0))
            data["padding"] = (int(t), int(r), int(b), int(left_cells))
        if self.resolved.outline:
            data["outline"] = self._downsample_color(str(self.resolved.outline), depth)
        if self.resolved.component_extras:
            data.update(self.resolved.component_extras)
        return data
