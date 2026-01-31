"""Cell-based rendering primitives for CLI output.

This module provides the core data structures for Rich-inspired cell-based
terminal rendering. Every cell is fully specified with character, foreground,
background, and attributes - no terminal state is trusted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ornata.definitions.dataclasses.styling import ANSIColor


@dataclass(slots=True, frozen=True)
class Segment:
    """A styled text segment - the primitive unit of CLI rendering.

    Like Rich's Segment, this represents a span of text with a complete style
    specification. Segments are stateless - they carry all style information
    needed to render them without reference to terminal state.

    Parameters
    ----------
    text : str
        The text content of this segment.
    fg : ANSIColor | None
        Foreground color (None = inherit from parent/cell).
    bg : ANSIColor | None
        Background color (None = inherit from parent/cell).
    bold : bool
        Bold attribute flag.
    dim : bool
        Dim/faint attribute flag.
    italic : bool
        Italic attribute flag.
    underline : bool
        Underline attribute flag.
    blink : bool
        Blink attribute flag.
    reverse : bool
        Reverse video attribute flag.
    strikethrough : bool
        Strikethrough attribute flag.

    Examples
    --------
    >>> from ornata.definitions.dataclasses.styling import ANSIColor
    >>> seg = Segment("Hello", fg=ANSIColor(255, 0, 0), bold=True)
    >>> seg.text
    'Hello'
    """

    text: str
    fg: ANSIColor | None = None
    bg: ANSIColor | None = None
    bold: bool = False
    dim: bool = False
    italic: bool = False
    underline: bool = False
    blink: bool = False
    reverse: bool = False
    strikethrough: bool = False

    def with_fg(self, fg: ANSIColor | None) -> Segment:
        """Return a new Segment with the specified foreground color."""
        return Segment(
            text=self.text,
            fg=fg,
            bg=self.bg,
            bold=self.bold,
            dim=self.dim,
            italic=self.italic,
            underline=self.underline,
            blink=self.blink,
            reverse=self.reverse,
            strikethrough=self.strikethrough,
        )

    def with_bg(self, bg: ANSIColor | None) -> Segment:
        """Return a new Segment with the specified background color."""
        return Segment(
            text=self.text,
            fg=self.fg,
            bg=bg,
            bold=self.bold,
            dim=self.dim,
            italic=self.italic,
            underline=self.underline,
            blink=self.blink,
            reverse=self.reverse,
            strikethrough=self.strikethrough,
        )

    def with_style(
        self,
        *,
        fg: ANSIColor | None = None,
        bg: ANSIColor | None = None,
        bold: bool = False,
        dim: bool = False,
        italic: bool = False,
        underline: bool = False,
        blink: bool = False,
        reverse: bool = False,
        strikethrough: bool = False,
    ) -> Segment:
        """Return a new Segment with merged style (None values preserve existing)."""
        return Segment(
            text=self.text,
            fg=fg if fg is not None else self.fg,
            bg=bg if bg is not None else self.bg,
            bold=bold or self.bold,
            dim=dim or self.dim,
            italic=italic or self.italic,
            underline=underline or self.underline,
            blink=blink or self.blink,
            reverse=reverse or self.reverse,
            strikethrough=strikethrough or self.strikethrough,
        )


@dataclass(slots=True)
class Cell:
    """A single terminal cell with complete style specification.

    Cells are the runtime truth of the terminal display. Each cell must be
    fully specified - no implicit inheritance at this level. The CellBuffer
    handles parent-to-child style propagation before creating cells.

    Parameters
    ----------
    char : str
        Single character to display (space for empty).
    fg : ANSIColor | None
        Foreground color (always set, never None in practice).
    bg : ANSIColor | None
        Background color (always set, never None in practice).
    bold : bool
        Bold attribute.
    dim : bool
        Dim/faint attribute.
    italic : bool
        Italic attribute.
    underline : bool
        Underline attribute.
    blink : bool
        Blink attribute.
    reverse : bool
        Reverse video attribute.
    strikethrough : bool
        Strikethrough attribute.

    Examples
    --------
    >>> from ornata.definitions.dataclasses.styling import ANSIColor
    >>> cell = Cell("X", fg=ANSIColor(255, 0, 0), bg=ANSIColor(0, 0, 0))
    """

    char: str = " "
    fg: ANSIColor | None = None
    bg: ANSIColor | None = None
    bold: bool = False
    dim: bool = False
    italic: bool = False
    underline: bool = False
    blink: bool = False
    reverse: bool = False
    strikethrough: bool = False

    def __post_init__(self) -> None:
        """Ensure char is exactly one character."""
        if len(self.char) != 1:
            raise ValueError(f"Cell char must be single character, got {self.char!r}")

    def with_char(self, char: str) -> Cell:
        """Return a new Cell with the specified character."""
        if len(char) != 1:
            raise ValueError(f"Cell char must be single character, got {char!r}")
        return Cell(
            char=char,
            fg=self.fg,
            bg=self.bg,
            bold=self.bold,
            dim=self.dim,
            italic=self.italic,
            underline=self.underline,
            blink=self.blink,
            reverse=self.reverse,
            strikethrough=self.strikethrough,
        )

    def with_fg(self, fg: ANSIColor | None) -> Cell:
        """Return a new Cell with the specified foreground color."""
        return Cell(
            char=self.char,
            fg=fg,
            bg=self.bg,
            bold=self.bold,
            dim=self.dim,
            italic=self.italic,
            underline=self.underline,
            blink=self.blink,
            reverse=self.reverse,
            strikethrough=self.strikethrough,
        )

    def with_bg(self, bg: ANSIColor | None) -> Cell:
        """Return a new Cell with the specified background color."""
        return Cell(
            char=self.char,
            fg=self.fg,
            bg=bg,
            bold=self.bold,
            dim=self.dim,
            italic=self.italic,
            underline=self.underline,
            blink=self.blink,
            reverse=self.reverse,
            strikethrough=self.strikethrough,
        )


@dataclass(slots=True)
class CellBuffer:
    """A 2D grid of Cells representing the terminal screen.

    The CellBuffer is the central data structure for Rich-inspired rendering.
    It maintains a complete grid where every cell has explicit styling.
    Background persistence is achieved by filling the entire grid with the
    root background before rendering widgets.

    Parameters
    ----------
    width : int
        Buffer width in cells.
    height : int
        Buffer height in cells.
    default_fg : ANSIColor | None
        Default foreground color for empty cells.
    default_bg : ANSIColor | None
        Default background color for empty cells.

    Attributes
    ----------
    _grid : list[list[Cell]]
        The 2D cell grid, row-major order.
    _dirty : set[tuple[int, int]]
        Set of (x, y) coordinates that have been modified.

    Examples
    --------
    >>> from ornata.definitions.dataclasses.styling import ANSIColor
    >>> buf = CellBuffer(80, 24, default_bg=ANSIColor(0, 0, 0))
    >>> buf.set_cell(0, 0, Cell("X", fg=ANSIColor(255, 0, 0), bg=ANSIColor(0, 0, 0)))
    """

    width: int
    height: int
    default_fg: ANSIColor | None = None
    default_bg: ANSIColor | None = None
    _grid: list[list[Cell]] = field(init=False, repr=False)
    _dirty: set[tuple[int, int]] = field(default_factory=set, repr=False)

    def __post_init__(self) -> None:
        """Initialize the cell grid with default colors."""
        self._grid = [
            [
                Cell(char=" ", fg=self.default_fg, bg=self.default_bg)
                for _ in range(self.width)
            ]
            for _ in range(self.height)
        ]

    def clear(self, bg: ANSIColor | None = None) -> None:
        """Clear the buffer, filling with the specified or default background.

        Parameters
        ----------
        bg : ANSIColor | None
            Background color to fill with. If None, uses default_bg.
        """
        fill_bg = bg if bg is not None else self.default_bg
        for y in range(self.height):
            for x in range(self.width):
                self._grid[y][x] = Cell(char=" ", fg=self.default_fg, bg=fill_bg)
                self._dirty.add((x, y))

    def get_cell(self, x: int, y: int) -> Cell | None:
        """Get the cell at the specified coordinates.

        Returns None if coordinates are out of bounds.
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return None
        return self._grid[y][x]

    def set_cell(self, x: int, y: int, cell: Cell) -> bool:
        """Set the cell at the specified coordinates.

        Parameters
        ----------
        x : int
            X coordinate (column).
        y : int
            Y coordinate (row).
        cell : Cell
            The cell to place.

        Returns
        -------
        bool
            True if the cell was set, False if out of bounds.
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        self._grid[y][x] = cell
        self._dirty.add((x, y))
        return True

    def write_segment(self, x: int, y: int, segment: Segment, inherited_bg: ANSIColor | None = None) -> int:
        """Write a segment to the buffer starting at (x, y).

        Each character in the segment becomes a cell with the segment's style.
        Background color is resolved: segment.bg > inherited_bg > default_bg.

        Parameters
        ----------
        x : int
            Starting X coordinate.
        y : int
            Y coordinate (row).
        segment : Segment
            The styled text segment to write.
        inherited_bg : ANSIColor | None
            Background color to inherit if segment has no bg.

        Returns
        -------
        int
            Number of characters written.
        """
        if not (0 <= y < self.height):
            return 0

        # Resolve background: segment > inherited > default
        resolved_bg = segment.bg if segment.bg is not None else inherited_bg
        if resolved_bg is None:
            resolved_bg = self.default_bg

        # Resolve foreground: segment > default
        resolved_fg = segment.fg if segment.fg is not None else self.default_fg

        chars_written = 0
        for i, char in enumerate(segment.text):
            col = x + i
            if col >= self.width:
                break

            cell = Cell(
                char=char,
                fg=resolved_fg,
                bg=resolved_bg,
                bold=segment.bold,
                dim=segment.dim,
                italic=segment.italic,
                underline=segment.underline,
                blink=segment.blink,
                reverse=segment.reverse,
                strikethrough=segment.strikethrough,
            )
            self._grid[y][col] = cell
            self._dirty.add((col, y))
            chars_written += 1

        return chars_written

    def fill_rect(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        char: str = " ",
        fg: ANSIColor | None = None,
        bg: ANSIColor | None = None,
    ) -> None:
        """Fill a rectangular region with the specified cell properties.

        Parameters
        ----------
        x, y : int
            Top-left corner of the rectangle.
        width, height : int
            Dimensions of the rectangle.
        char : str
            Character to fill with (default: space).
        fg : ANSIColor | None
            Foreground color (None = use default).
        bg : ANSIColor | None
            Background color (None = use default).
        """
        if len(char) != 1:
            raise ValueError(f"Fill char must be single character, got {char!r}")

        resolved_fg = fg if fg is not None else self.default_fg
        resolved_bg = bg if bg is not None else self.default_bg

        x_start = max(0, x)
        x_end = min(self.width, x + width)
        y_start = max(0, y)
        y_end = min(self.height, y + height)

        for row in range(y_start, y_end):
            for col in range(x_start, x_end):
                self._grid[row][col] = Cell(
                    char=char,
                    fg=resolved_fg,
                    bg=resolved_bg,
                )
                self._dirty.add((col, row))

    def get_dirty_cells(self) -> list[tuple[int, int, Cell]]:
        """Get all dirty cells as (x, y, cell) tuples.

        Returns
        -------
        list[tuple[int, int, Cell]]
            List of modified cells with their coordinates.
        """
        result = []
        for x, y in sorted(self._dirty):
            if 0 <= x < self.width and 0 <= y < self.height:
                result.append((x, y, self._grid[y][x]))
        return result

    def clear_dirty(self) -> None:
        """Clear the dirty cell tracking."""
        self._dirty.clear()

    def is_dirty(self) -> bool:
        """Check if any cells have been modified since last clear."""
        return len(self._dirty) > 0

    def resize(self, width: int, height: int) -> None:
        """Resize the buffer, preserving existing content where possible.

        Parameters
        ----------
        width : int
            New width.
        height : int
            New height.
        """
        if width == self.width and height == self.height:
            return

        # Create new grid
        new_grid: list[list[Cell]] = [
            [
                Cell(char=" ", fg=self.default_fg, bg=self.default_bg)
                for _ in range(width)
            ]
            for _ in range(height)
        ]

        # Copy existing content
        copy_width = min(self.width, width)
        copy_height = min(self.height, height)
        for y in range(copy_height):
            for x in range(copy_width):
                new_grid[y][x] = self._grid[y][x]
                self._dirty.add((x, y))

        self.width = width
        self.height = height
        self._grid = new_grid


__all__ = [
    "Cell",
    "CellBuffer",
    "Segment",
]
