"""ANSI output generation for cell-based rendering.

This module converts CellBuffer contents to ANSI escape sequences for terminal
output. Like Rich, every cell is fully specified - we emit complete style
codes for each cell without trusting terminal state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ornata.definitions.dataclasses.styling import ANSIColor
    from ornata.rendering.backends.cli.cells import Cell, CellBuffer


@dataclass(slots=True)
class ANSIOutput:
    """Container for ANSI-formatted output with metadata.

    Attributes
    ----------
    text : str
        The complete ANSI-encoded string.
    width : int
        Width in characters.
    height : int
        Height in lines.
    has_colors : bool
        Whether the output contains ANSI sequences.
    """

    text: str
    width: int
    height: int
    has_colors: bool = False


@dataclass(slots=True)
class ANSIRenderer:
    """Renders CellBuffer contents to ANSI escape sequences.

    This renderer follows Rich's principle: every cell is fully specified.
    No terminal state is trusted. For each cell, we emit complete style codes
    (FG, BG, attrs) before the character.

    The renderer optimizes by only emitting codes when style changes between
    adjacent cells, but conceptually each cell is independent.

    Parameters
    ----------
    use_truecolor : bool
        Use 24-bit RGB colors (\x1b[38;2;r;g;bm) instead of 256-color palette.
    """

    use_truecolor: bool = True

    # ANSI codes for attributes
    _RESET: str = field(default="\x1b[0m", repr=False)
    _BOLD: str = field(default="\x1b[1m", repr=False)
    _DIM: str = field(default="\x1b[2m", repr=False)
    _ITALIC: str = field(default="\x1b[3m", repr=False)
    _UNDERLINE: str = field(default="\x1b[4m", repr=False)
    _BLINK: str = field(default="\x1b[5m", repr=False)
    _REVERSE: str = field(default="\x1b[7m", repr=False)
    _STRIKETHROUGH: str = field(default="\x1b[9m", repr=False)

    def render(self, buffer: CellBuffer) -> ANSIOutput:
        """Render a CellBuffer to ANSI-formatted text.

        Parameters
        ----------
        buffer : CellBuffer
            The cell buffer to render.

        Returns
        -------
        ANSIOutput
            Formatted output with metadata.
        """
        lines: list[str] = []
        has_colors = False

        for y in range(buffer.height):
            line = self._render_line(buffer, y)
            if line:
                has_colors = has_colors or "\x1b[" in line
            lines.append(line)

        # Join with newlines and ensure final newline
        text = "\n".join(lines) + "\n"

        return ANSIOutput(
            text=text,
            width=buffer.width,
            height=buffer.height,
            has_colors=has_colors,
        )

    def _render_line(self, buffer: CellBuffer, y: int) -> str:
        """Render a single line of the buffer.

        Parameters
        ----------
        buffer : CellBuffer
            The cell buffer.
        y : int
            Line index.

        Returns
        -------
        str
            ANSI-formatted line (without trailing newline).
        """
        result_parts: list[str] = []
        current_fg: ANSIColor | None = None
        current_bg: ANSIColor | None = None
        current_bold = False
        current_italic = False
        current_underline = False
        current_strikethrough = False

        for x in range(buffer.width):
            cell = buffer.get_cell(x, y)
            if cell is None:
                continue

            # Check if any style attributes changed
            style_changed = (
                cell.fg != current_fg
                or cell.bg != current_bg
                or cell.bold != current_bold
                or cell.italic != current_italic
                or cell.underline != current_underline
                or cell.strikethrough != current_strikethrough
            )

            if style_changed:
                # Emit reset and new style codes
                codes: list[str] = []

                # Always reset when changing to avoid bleeding
                codes.append("0")

                # Foreground color
                if cell.fg is not None:
                    codes.append(self._fg_code(cell.fg))

                # Background color
                if cell.bg is not None:
                    codes.append(self._bg_code(cell.bg))

                # Attributes
                if cell.bold:
                    codes.append("1")
                if cell.dim:
                    codes.append("2")
                if cell.italic:
                    codes.append("3")
                if cell.underline:
                    codes.append("4")
                if cell.blink:
                    codes.append("5")
                if cell.reverse:
                    codes.append("7")
                if cell.strikethrough:
                    codes.append("9")

                result_parts.append(f"\x1b[{';'.join(codes)}m")

                # Update current state
                current_fg = cell.fg
                current_bg = cell.bg
                current_bold = cell.bold
                current_italic = cell.italic
                current_underline = cell.underline
                current_strikethrough = cell.strikethrough

            # Add the character
            result_parts.append(cell.char)

        # Reset at end of line to prevent bleeding to next line
        if result_parts and (current_fg is not None or current_bg is not None or current_bold or current_italic or current_underline or current_strikethrough):
            result_parts.append(self._RESET)

        return "".join(result_parts)

    def _fg_code(self, color: ANSIColor) -> str:
        """Generate ANSI foreground color code.

        Parameters
        ----------
        color : ANSIColor
            The color to encode.

        Returns
        -------
        str
            ANSI foreground color code (e.g., "38;2;255;0;0" for truecolor).
        """
        if self.use_truecolor:
            return f"38;2;{color.red};{color.green};{color.blue}"
        # Fall back to 256-color palette
        return f"38;5;{color.to_ansi_256()}"

    def _bg_code(self, color: ANSIColor) -> str:
        """Generate ANSI background color code.

        Parameters
        ----------
        color : ANSIColor
            The color to encode.

        Returns
        -------
        str
            ANSI background color code (e.g., "48;2;255;0;0" for truecolor).
        """
        if self.use_truecolor:
            return f"48;2;{color.red};{color.green};{color.blue}"
        # Fall back to 256-color palette
        return f"48;5;{color.to_ansi_256()}"

    def render_cell(self, cell: Cell) -> str:
        """Render a single cell to ANSI string.

        This is useful for debugging or when you need individual cell output.

        Parameters
        ----------
        cell : Cell
            The cell to render.

        Returns
        -------
        str
            ANSI-formatted single character.
        """
        codes: list[str] = ["0"]  # Always reset first

        if cell.fg is not None:
            codes.append(self._fg_code(cell.fg))
        if cell.bg is not None:
            codes.append(self._bg_code(cell.bg))
        if cell.bold:
            codes.append("1")
        if cell.italic:
            codes.append("3")
        if cell.underline:
            codes.append("4")
        if cell.strikethrough:
            codes.append("9")

        style_seq = f"\x1b[{';'.join(codes)}m"
        return f"{style_seq}{cell.char}{self._RESET}"


# Convenience function for quick rendering
def render_buffer(buffer: CellBuffer, *, use_truecolor: bool = True) -> str:
    """Quick render a CellBuffer to ANSI string.

    Parameters
    ----------
    buffer : CellBuffer
        The buffer to render.
    use_truecolor : bool
        Use 24-bit colors (default: True).

    Returns
    -------
    str
        ANSI-formatted text.
    """
    renderer = ANSIRenderer(use_truecolor=use_truecolor)
    return renderer.render(buffer).text
