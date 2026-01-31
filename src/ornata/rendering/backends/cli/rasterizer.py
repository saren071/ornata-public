"""Node rasterization for CLI rendering.

This module converts GuiNode trees to cell-based representations,
handling parent-to-child style inheritance and spatial composition.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import GuiNode
    from ornata.definitions.dataclasses.styling import ANSIColor, BackendStylePayload
    from ornata.rendering.backends.cli.cells import CellBuffer, Segment


logger = get_logger(__name__)


@dataclass(slots=True)
class RasterContext:
    """Context for rasterizing a node hierarchy.

    Maintains the current style state during depth-first traversal,
    handling parent-to-child inheritance for colors.

    Attributes
    ----------
    inherited_fg : ANSIColor | None
        Foreground color inherited from parent.
    inherited_bg : ANSIColor | None
        Background color inherited from parent.
    bold : bool
        Bold attribute state.
    dim : bool
        Dim attribute state.
    italic : bool
        Italic attribute state.
    underline : bool
        Underline attribute state.
    blink : bool
        Blink attribute state.
    reverse : bool
        Reverse attribute state.
    strikethrough : bool
        Strikethrough attribute state.
    """

    inherited_fg: ANSIColor | None = None
    inherited_bg: ANSIColor | None = None
    bold: bool = False
    dim: bool = False
    italic: bool = False
    underline: bool = False
    blink: bool = False
    reverse: bool = False
    strikethrough: bool = False

    def with_style(self, style: BackendStylePayload | None) -> RasterContext:
        """Create a child context with merged style.

        Child style overrides parent style where explicitly set.
        """
        if style is None or style.style is None:
            return RasterContext(
                inherited_fg=self.inherited_fg,
                inherited_bg=self.inherited_bg,
                bold=self.bold,
                dim=self.dim,
                italic=self.italic,
                underline=self.underline,
                blink=self.blink,
                reverse=self.reverse,
                strikethrough=self.strikethrough,
            )

        resolved = style.style

        # Extract colors from resolved style (already converted to ANSI strings by style system)
        fg = self._extract_color(resolved.color)
        bg = self._extract_color(resolved.background)

        # Inheritance: explicit > parent > None
        new_fg = fg if fg is not None else self.inherited_fg
        new_bg = bg if bg is not None else self.inherited_bg

        # Attributes: accumulate (parent OR child)
        # Note: This is a design choice - we could also have child override parent
        return RasterContext(
            inherited_fg=new_fg,
            inherited_bg=new_bg,
            bold=self.bold or self._extract_bool(resolved, "bold"),
            dim=self.dim or self._extract_bool(resolved, "dim"),
            italic=self.italic or self._extract_bool(resolved, "italic"),
            underline=self.underline or self._extract_bool(resolved, "underline"),
            blink=self.blink or self._extract_bool(resolved, "blink"),
            reverse=self.reverse or self._extract_bool(resolved, "reverse"),
            strikethrough=self.strikethrough or self._extract_bool(resolved, "strikethrough"),
        )

    def _extract_color(self, color_value: Any) -> ANSIColor | None:
        """Extract ANSIColor from style value.

        The styling system converts colors to ANSI escape sequences for CLI backends.
        We need to parse these strings to extract RGB values.
        """
        if color_value is None:
            return None

        from ornata.definitions.dataclasses.styling import ANSIColor

        # If it's already an ANSIColor, return it
        if isinstance(color_value, ANSIColor):
            return color_value

        # If it's a string (ANSI escape sequence), parse it
        if isinstance(color_value, str):
            return self._parse_ansi_color(color_value)

        return None

    def _parse_ansi_color(self, ansi_str: str) -> ANSIColor | None:
        """Parse ANSI escape sequence to extract RGB values.

        Supports:
        - Truecolor: \x1b[38;2;R;G;Bm or \x1b[48;2;R;G;Bm
        - 256-color: \x1b[38;5;Nm or \x1b[48;5;Nm
        - 16-color: \x1b[30-37m, \x1b[90-97m (fg) or \x1b[40-47m, \x1b[100-107m (bg)
        """
        from ornata.definitions.dataclasses.styling import ANSIColor

        if not ansi_str or not ansi_str.startswith("\x1b["):
            return None

        # Remove escape prefix and suffix
        # \x1b[38;2;R;G;Bm -> 38;2;R;G;B
        content = ansi_str[2:]  # Skip \x1b[
        if content.endswith("m"):
            content = content[:-1]

        parts = content.split(";")
        if not parts:
            return None

        try:
            # Truecolor: 38;2;R;G;B (fg) or 48;2;R;G;B (bg)
            if len(parts) >= 5 and parts[1] == "2":
                r = int(parts[2])
                g = int(parts[3])
                b = int(parts[4])
                return ANSIColor(r, g, b)

            # 256-color: 38;5;N (fg) or 48;5;N (bg)
            if len(parts) >= 3 and parts[1] == "5":
                code = int(parts[2])
                r, g, b = self._ansi_256_to_rgb(code)
                return ANSIColor(r, g, b)

            # 16-color standard codes
            if len(parts) == 1:
                code = int(parts[0])
                r, g, b = self._ansi_16_to_rgb(code)
                return ANSIColor(r, g, b)

        except (ValueError, IndexError):
            pass

        return None

    def _ansi_256_to_rgb(self, code: int) -> tuple[int, int, int]:
        """Convert ANSI 256-color code to RGB."""
        if code < 16:
            # Standard 16 colors
            return self._ansi_16_to_rgb(code)
        elif code < 232:
            # 6x6x6 color cube (16-231)
            code -= 16
            r = (code // 36) * 51
            g = ((code % 36) // 6) * 51
            b = (code % 6) * 51
            return (r, g, b)
        else:
            # Grayscale (232-255)
            gray = (code - 232) * 10 + 8
            return (gray, gray, gray)

    def _ansi_16_to_rgb(self, code: int) -> tuple[int, int, int]:
        """Convert ANSI 16-color code to RGB."""
        # Standard ANSI 16 colors
        colors = [
            (0, 0, 0),       # 0: Black
            (170, 0, 0),     # 1: Red
            (0, 170, 0),     # 2: Green
            (170, 85, 0),    # 3: Yellow
            (0, 0, 170),     # 4: Blue
            (170, 0, 170),   # 5: Magenta
            (0, 170, 170),   # 6: Cyan
            (170, 170, 170), # 7: White/Gray
            (85, 85, 85),    # 8: Bright Black
            (255, 85, 85),   # 9: Bright Red
            (85, 255, 85),   # 10: Bright Green
            (255, 255, 85),  # 11: Bright Yellow
            (85, 85, 255),   # 12: Bright Blue
            (255, 85, 255),  # 13: Bright Magenta
            (85, 255, 255),  # 14: Bright Cyan
            (255, 255, 255), # 15: Bright White
        ]
        if 0 <= code < 16:
            return colors[code]
        # Handle foreground (30-37, 90-97) and background (40-47, 100-107) codes
        if 30 <= code <= 37:
            return colors[code - 30]
        if 40 <= code <= 47:
            return colors[code - 40]
        if 90 <= code <= 97:
            return colors[code - 82]  # 90 -> 8, 97 -> 15
        if 100 <= code <= 107:
            return colors[code - 92]  # 100 -> 8, 107 -> 15
        return (128, 128, 128)  # Default gray

    def _extract_bool(self, style: Any, attr: str) -> bool:
        """Extract boolean attribute from style."""
        val = getattr(style, attr, None)
        if isinstance(val, bool):
            return val
        # Handle string values like "bold" in font-weight
        if attr == "bold" and hasattr(style, "weight"):
            weight = getattr(style, "weight", None)
            if isinstance(weight, str):
                return "bold" in weight.lower()
            if isinstance(weight, int):
                return weight >= 700
        return False


class NodeRasterizer:
    """Rasterizes GuiNode trees to CellBuffer.

    This implements the Rich-inspired rendering model:
    - Every cell is fully specified
    - Parent background propagates to children
    - Spatial composition only (no style cascade beyond inheritance)
    """

    def __init__(self, width: int, height: int, default_bg: ANSIColor | None = None) -> None:
        """Initialize the rasterizer.

        Parameters
        ----------
        width : int
            Target buffer width.
        height : int
            Target buffer height.
        default_bg : ANSIColor | None
            Default background color for the entire screen.
        """
        self.width = width
        self.height = height
        self.default_bg = default_bg

    def rasterize(self, root: GuiNode) -> CellBuffer:
        """Rasterize a GuiNode tree to a CellBuffer.

        Parameters
        ----------
        root : GuiNode
            The root node of the tree.

        Returns
        -------
        CellBuffer
            The rasterized cell buffer.
        """
        from ornata.rendering.backends.cli.cells import CellBuffer

        buffer = CellBuffer(
            width=self.width,
            height=self.height,
            default_bg=self.default_bg,
        )

        # Clear with root background
        buffer.clear(self.default_bg)

        # Create root context
        context = RasterContext(inherited_bg=self.default_bg)

        # Rasterize the tree
        self._rasterize_node(buffer, root, context)

        return buffer

    def _rasterize_node(self, buffer: CellBuffer, node: GuiNode, context: RasterContext) -> None:
        """Rasterize a single node and its children."""
        if not getattr(node, "visible", True):
            return

        # Get node bounds from layout
        x = getattr(node, "x", 0)
        y = getattr(node, "y", 0)
        width = getattr(node, "width", 0)
        height = getattr(node, "height", 0)

        comp_name = getattr(node, "component_name", "unknown")
        if "action" in comp_name.lower() or "button" in comp_name.lower() or "input" in comp_name.lower() or "command" in comp_name.lower():
            logger.info(f"[rasterizer] {comp_name}: pos=({x},{y}) size={width}x{height} visible={getattr(node, 'visible', True)}")
        else:
            logger.debug(f"[rasterizer] {comp_name}: pos=({x},{y}) size={width}x{height}")

        if width <= 0 or height <= 0:
            logger.debug(f"[rasterizer] {comp_name}: skipping (zero size)")
            return

        # Get backend style payload (pre-resolved by styling system)
        metadata = getattr(node, "metadata", None) or {}
        backend_payload = metadata.get("backend_style")

        # Debug: log what we got
        if backend_payload and backend_payload.style:
            style = backend_payload.style
            logger.debug(f"[rasterizer] {comp_name}: color={style.color!r}, background={style.background!r}")
        else:
            logger.debug(f"[rasterizer] {comp_name}: no backend_style")

        # Create child context with this node's style
        node_context = context.with_style(backend_payload)

        # Debug: log context after merge
        logger.debug(f"[rasterizer] {comp_name}: context fg={node_context.inherited_fg}, bg={node_context.inherited_bg}")

        # Rasterize this node's background (if any)
        if node_context.inherited_bg is not None:
            buffer.fill_rect(x, y, width, height, char=" ", bg=node_context.inherited_bg)
            logger.debug(f"[rasterizer] {comp_name}: filled rect ({x},{y}) {width}x{height} with bg")

        # Rasterize borders if present
        self._rasterize_borders(buffer, node, x, y, width, height, node_context)

        # Rasterize content
        self._rasterize_content(buffer, node, x, y, width, height, node_context)

        # Recurse to children
        children = getattr(node, "children", []) or []
        for child in children:
            self._rasterize_node(buffer, child, node_context)

    def _rasterize_borders(
        self,
        buffer: CellBuffer,
        node: GuiNode,
        x: int,
        y: int,
        width: int,
        height: int,
        context: RasterContext,
    ) -> None:
        """Rasterize node borders using box-drawing characters."""
        from ornata.definitions.dataclasses.styling import ANSIColor
        from ornata.definitions.unicode_assets import BORDER_STYLES
        from ornata.rendering.backends.cli.cells import Cell

        # Determine border width and style
        border_width = 0.0
        border_from_style = getattr(getattr(node, "style", None), "border", None)
        if border_from_style is not None:
            border_width = max(border_width, getattr(border_from_style, "width", 0.0) or 0.0)

        metadata = getattr(node, "metadata", None) or {}
        metadata_border_width = metadata.get("border_width")
        if isinstance(metadata_border_width, (int, float)):
            border_width = max(border_width, float(metadata_border_width))

        if border_width <= 0:
            return

        # Determine border emphasis (thick vs thin)
        emphasize = False
        if isinstance(metadata.get("border_emphasize"), bool):
            emphasize = metadata["border_emphasize"]
        elif border_width >= 2.0:
            emphasize = True

        # Select border characters
        border_chars = BORDER_STYLES.get("heavy" if emphasize else "light", BORDER_STYLES["light"])

        # Get border color (from style or inherit from context)
        border_color = self._extract_border_color(node, context)
        fg_color = border_color if border_color is not None else context.inherited_fg
        bg_color = context.inherited_bg

        # Draw border lines
        x1 = x + width - 1
        y1 = y + height - 1

        # Top edge
        for col in range(x + 1, x1):
            if 0 <= col < buffer.width and 0 <= y < buffer.height:
                buffer.set_cell(col, y, Cell(border_chars["h"], fg=fg_color, bg=bg_color))

        # Bottom edge
        for col in range(x + 1, x1):
            if 0 <= col < buffer.width and 0 <= y1 < buffer.height:
                buffer.set_cell(col, y1, Cell(border_chars["h"], fg=fg_color, bg=bg_color))

        # Left edge
        for row in range(y + 1, y1):
            if 0 <= x < buffer.width and 0 <= row < buffer.height:
                buffer.set_cell(x, row, Cell(border_chars["v"], fg=fg_color, bg=bg_color))

        # Right edge
        for row in range(y + 1, y1):
            if 0 <= x1 < buffer.width and 0 <= row < buffer.height:
                buffer.set_cell(x1, row, Cell(border_chars["v"], fg=fg_color, bg=bg_color))

        # Corners
        corners = [
            (x, y, "tl"),
            (x1, y, "tr"),
            (x, y1, "bl"),
            (x1, y1, "br"),
        ]
        for cx, cy, key in corners:
            if 0 <= cx < buffer.width and 0 <= cy < buffer.height:
                buffer.set_cell(cx, cy, Cell(border_chars[key], fg=fg_color, bg=bg_color))

    def _extract_border_color(self, node: GuiNode, context: RasterContext) -> ANSIColor | None:
        """Extract border color from node style."""
        from ornata.definitions.dataclasses.styling import ANSIColor

        style = getattr(node, "style", None)
        if style is None:
            return None

        # Try border_color first
        border_color = getattr(style, "border_color", None)
        if border_color is not None:
            if isinstance(border_color, ANSIColor):
                return border_color
            # Handle string ANSI codes if needed

        # Fall back to regular color
        color = getattr(style, "color", None)
        if isinstance(color, ANSIColor):
            return color

        return None

    def _rasterize_content(
        self,
        buffer: CellBuffer,
        node: GuiNode,
        x: int,
        y: int,
        width: int,
        height: int,
        context: RasterContext,
    ) -> None:
        """Rasterize node content (text, tables, etc.)."""
        from ornata.rendering.backends.cli.cells import Segment

        # Get inner content area (inside borders if any)
        inner_x = x + 1
        inner_y = y + 1
        inner_width = max(1, width - 2)
        inner_height = max(1, height - 2)

        # Check for table data
        columns = getattr(node, "columns", None)
        rows = getattr(node, "rows", None)
        if columns and rows:
            self._rasterize_table(
                buffer, columns, rows, inner_x, inner_y, inner_width, inner_height, context
            )
            return

        # Check for text content
        text = self._extract_text(node)
        if text:
            self._rasterize_text(
                buffer, text, inner_x, inner_y, inner_width, inner_height, context
            )

    def _extract_text(self, node: GuiNode) -> str | None:
        """Extract text content from a node."""
        # Direct text attribute
        text = getattr(node, "text", None)
        if text:
            return str(text)

        # Content object attributes
        content = getattr(node, "content", None)
        if content is not None:
            for attr in ("title", "subtitle", "body", "text", "caption"):
                val = getattr(content, attr, None)
                if isinstance(val, str) and val.strip():
                    return val.strip()

        # Placeholder
        placeholder = getattr(content, "placeholder", None) if content else None
        if placeholder:
            return f"[{placeholder}]"

        # Status
        status = getattr(node, "status", None)
        if status:
            return status

        return None

    def _rasterize_text(
        self,
        buffer: CellBuffer,
        text: str,
        x: int,
        y: int,
        width: int,
        height: int,
        context: RasterContext,
    ) -> None:
        """Rasterize text content with word wrapping."""
        from textwrap import wrap

        from ornata.definitions.dataclasses.styling import ANSIColor
        from ornata.rendering.backends.cli.cells import Segment

        # Resolve final colors for this content
        fg = context.inherited_fg
        bg = context.inherited_bg

        lines: list[str] = []
        for paragraph in text.splitlines() or [""]:
            if not paragraph.strip():
                lines.append("")
                continue
            wrapped = wrap(
                paragraph,
                width=width,
                drop_whitespace=True,
                replace_whitespace=False,
            )
            lines.extend(wrapped or [""])

        # Write lines to buffer
        for row_idx, line in enumerate(lines[:height]):
            if row_idx >= height:
                break
            segment = Segment(
                text=line[:width].ljust(width),
                fg=fg,
                bg=bg,
                bold=context.bold,
                dim=context.dim,
                italic=context.italic,
                underline=context.underline,
                blink=context.blink,
                reverse=context.reverse,
                strikethrough=context.strikethrough,
            )
            buffer.write_segment(x, y + row_idx, segment, inherited_bg=bg)

    def _rasterize_table(
        self,
        buffer: CellBuffer,
        columns: list[str],
        rows: list[list[Any]],
        x: int,
        y: int,
        width: int,
        height: int,
        context: RasterContext,
    ) -> None:
        """Rasterize table content."""
        from ornata.definitions.dataclasses.styling import ANSIColor
        from ornata.rendering.backends.cli.cells import Segment

        if height < 2:
            return

        fg = context.inherited_fg
        bg = context.inherited_bg

        # Format header
        slots = max(1, len(columns))
        spacer = 1 if slots > 1 else 0
        cell_width = max(1, (width - (spacer * (slots - 1))) // slots)

        header_cells = [str(col).strip()[:cell_width].ljust(cell_width) for col in columns]
        header_line = (" " * spacer).join(header_cells)[:width]

        # Write header
        header_segment = Segment(
            text=header_line,
            fg=fg,
            bg=bg,
            bold=True,  # Headers are bold
            dim=context.dim,
            italic=context.italic,
            underline=context.underline,
            blink=context.blink,
            reverse=context.reverse,
            strikethrough=context.strikethrough,
        )
        buffer.write_segment(x, y, header_segment, inherited_bg=bg)

        # Separator line
        separator = "-" * min(len(header_line.replace("\x1b[", "").replace("m", "")), width)
        sep_segment = Segment(
            text=separator[:width].ljust(width),
            fg=fg,
            bg=bg,
            bold=context.bold,
            dim=context.dim,
            italic=context.italic,
            underline=context.underline,
            blink=context.blink,
            reverse=context.reverse,
            strikethrough=context.strikethrough,
        )
        if height > 1:
            buffer.write_segment(x, y + 1, sep_segment, inherited_bg=bg)

        # Data rows
        row_y = y + 2
        for row in rows:
            if row_y >= y + height:
                break
            row_cells = [str(cell).strip()[:cell_width].ljust(cell_width) for cell in row]
            row_line = (" " * spacer).join(row_cells)[:width]
            row_segment = Segment(
                text=row_line,
                fg=fg,
                bg=bg,
                bold=context.bold,
                dim=context.dim,
                italic=context.italic,
                underline=context.underline,
                blink=context.blink,
                reverse=context.reverse,
                strikethrough=context.strikethrough,
            )
            buffer.write_segment(x, row_y, row_segment, inherited_bg=bg)
            row_y += 1


__all__ = [
    "NodeRasterizer",
    "RasterContext",
]
