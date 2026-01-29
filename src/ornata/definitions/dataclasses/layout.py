""" Layout Dataclasses for Ornata """

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ornata.definitions.enums import BackendTarget, RendererType

if TYPE_CHECKING:
    from ornata.api.exports.layout import LayoutNode
    from ornata.definitions.dataclasses.rendering import GuiNode
    from ornata.definitions.type_alias import AlignItems, FlexDirection, JustifyContent


@dataclass(slots=True, frozen=True)
class Bounds:
    """Bounding box for layout calculations."""
    x: float
    y: float
    width: float
    height: float

    def to_backend_units(self, backend_type: BackendTarget) -> Bounds:
        """Convert bounds to renderer-specific units."""
        if backend_type == BackendTarget.CLI:
            # Convert pixels to cells (assuming 8x16 font)
            return Bounds(
                x=self.x / 8,
                y=self.y / 16,
                width=self.width / 8,
                height=self.height / 16,
            )
        return self


@dataclass(slots=True)
class LayoutResult:
    """Result of a layout calculation."""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0


@dataclass
class SpatialIndexEntry:
    """Entry in spatial index for layout optimization."""
    component_id: str
    bounds: Bounds
    layer: int = 0


@dataclass
class LayoutDebugInfo:
    """Debug information for layout computations."""
    node: LayoutNode
    result: LayoutResult
    cache_hit: bool = False
    computation_time: float = 0.0
    child_count: int = 0
    depth: int = 0


@dataclass(slots=True)
class LayoutStyle:
    """Style properties for layout calculations."""
    width: int | None = None
    height: int | None = None
    min_width: int | None = None
    min_height: int | None = None
    max_width: int | None = None
    max_height: int | None = None
    flex_grow: float = 0.0
    flex_shrink: float = 1.0
    flex_basis: int | None = None
    margin: int = 0
    padding: int = 0
    direction: FlexDirection = "row"
    wrap: bool = False
    gap: int = 0
    justify: JustifyContent = "start"
    align: AlignItems = "stretch"
    display: str = "block"
    flex_direction: FlexDirection | None = None
    # Grid layout properties
    grid_template_columns: str | None = None
    grid_template_rows: str | None = None
    grid_column_gap: int = 0
    grid_row_gap: int = 0
    # Positioning properties
    position: str = "static"
    top: int | None = None
    right: int | None = None
    bottom: int | None = None
    left: int | None = None
    # Box model enhancements
    margin_top: int | None = None
    margin_right: int | None = None
    margin_bottom: int | None = None
    margin_left: int | None = None
    padding_top: int | None = None
    padding_right: int | None = None
    padding_bottom: int | None = None
    padding_left: int | None = None
    # Overflow and scrolling properties
    overflow: str = "visible"
    overflow_x: str | None = None
    overflow_y: str | None = None

    def __post_init__(self) -> None:
        """Normalise alias fields after dataclass construction."""
        if self.flex_direction is not None:
            self.direction = self.flex_direction
        else:
            self.flex_direction = self.direction


@dataclass(slots=True, frozen=True)
class LayoutConstraints:
    """Describes layout constraints for a component."""
    min_width: float | None = None
    max_width: float | None = None
    min_height: float | None = None
    max_height: float | None = None


@dataclass(slots=True)
class LayoutInput:
    """Input payload for layout algorithms."""
    node: GuiNode
    bounds: Bounds
    renderer_type: RendererType


@dataclass(slots=True)
class VirtualScrollConfig:
    """Configuration for virtual scrolling behavior."""
    item_height: int | None = None
    viewport_height: int = 20
    viewport_width: int = 80
    overscan: int = 5
    scroll_offset: int = 0
    total_items: int = 0


@dataclass(slots=True)
class VirtualScrollState:
    """Current state of virtual scrolling."""
    visible_start: int = 0
    visible_end: int = 0
    rendered_items: list[tuple[int, LayoutNode]] = field(default_factory=list)
    total_height: int = 0
    item_heights: list[int] = field(default_factory=list)

__all__ = [
    "Bounds",
    "LayoutConstraints",
    "LayoutDebugInfo",
    "LayoutInput",
    "LayoutResult",
    "LayoutStyle",
    "SpatialIndexEntry",
    "VirtualScrollConfig",
    "VirtualScrollState",
]
