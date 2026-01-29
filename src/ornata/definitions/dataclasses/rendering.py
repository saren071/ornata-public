""" Rendering Dataclasses for Ornata """

from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass, field
from textwrap import wrap
from typing import TYPE_CHECKING, Any

from ornata.definitions.dataclasses.components import ComponentAccessibility, ComponentContent, ComponentDataBinding, ComponentKind, ComponentPlacement, ComponentRenderHints, InteractionDescriptor
from ornata.definitions.dataclasses.styling import Color, TextStyle
from ornata.definitions.enums import BackendTarget, BlendMode, FrameState, InputEventType, RendererType, SignalType, TerminalCapability, TerminalType
from ornata.definitions.flags import RenderCapability
from ornata.definitions.unicode_assets import BORDER_STYLES

if TYPE_CHECKING:
    from ornata.api.exports.events import EventBus
    from ornata.definitions.protocols import LayoutStyleProtocol, ResolvedStyleProtocol

def _default_border_chars() -> dict[str, str]:
    return dict(BORDER_STYLES.get("light", {}))

def _default_emphasize_chars() -> dict[str, str]:
    return dict(BORDER_STYLES.get("heavy", BORDER_STYLES.get("light", {})))

@dataclass(slots=True)
class UnicodeCanvas:
    """Utility canvas that accumulates Unicode characters for terminal output."""
    width: int
    height: int
    border_chars: dict[str, str] = field(default_factory=_default_border_chars)
    emphasize_chars: dict[str, str] = field(default_factory=_default_emphasize_chars)
    _grid: list[list[str]] = field(init=False)

    def __post_init__(self) -> None:
        self._grid = [[" " for _ in range(self.width)] for _ in range(self.height)]

    def draw_panel(self, rect: tuple[int, int, int, int], *, label: str | None = None, emphasize: bool = False) -> None:
        bounds = self._clip_rect(rect)
        if bounds is None:
            return
        glyphs = self._select_border_chars(emphasize)
        x0, y0, x1, y1 = bounds
        if x1 <= x0 or y1 <= y0:
            self._plot(x0, y0, glyphs["tl"])
            return
        for x in range(x0 + 1, x1):
            self._plot(x, y0, glyphs["h"])
            self._plot(x, y1, glyphs["h"])
        for y in range(y0 + 1, y1):
            self._plot(x0, y, glyphs["v"])
            self._plot(x1, y, glyphs["v"])
        self._plot(x0, y0, glyphs["tl"])
        self._plot(x1, y0, glyphs["tr"])
        self._plot(x0, y1, glyphs["bl"])
        self._plot(x1, y1, glyphs["br"])
        if label:
            trimmed = label[: max(0, (x1 - x0) - 1)]
            if trimmed:
                self._write(x0 + 1, y0, f" {trimmed}")

    def draw_text_block(self, rect: tuple[int, int, int, int], text: str) -> None:
        bounds = self._clip_rect(rect)
        if bounds is None:
            return
        x0, y0, x1, y1 = bounds
        max_width = max(1, x1 - x0 + 1)
        max_height = max(1, y1 - y0 + 1)
        lines: list[str] = []
        for paragraph in text.splitlines() or [""]:
            if not paragraph.strip():
                lines.append("")
                continue
            wrapped = wrap(
                paragraph,
                width=max_width,
                drop_whitespace=True,
                replace_whitespace=False,
            )
            lines.extend(wrapped or [""])
        for row_idx, line in enumerate(lines[:max_height]):
            self._write(x0, y0 + row_idx, line[:max_width].ljust(max_width))

    def draw_table(self, rect: tuple[int, int, int, int], columns: list[str], rows: list[list[str]]) -> None:
        bounds = self._clip_rect(rect)
        if bounds is None:
            return
        x0, y0, x1, y1 = bounds
        max_width = max(1, x1 - x0 + 1)
        max_height = max(1, y1 - y0 + 1)
        if max_height < 2:
            return
        grid_lines: list[str] = []
        formatted_header = self._format_row(columns, max_width)
        grid_lines.append(formatted_header)
        separator = self.border_chars["h"]
        grid_lines.append(separator * min(len(formatted_header), max_width))
        for row in rows:
            grid_lines.append(self._format_row(row, max_width))
            if len(grid_lines) >= max_height:
                break
        for offset, line in enumerate(grid_lines[:max_height]):
            self._write(x0, y0 + offset, line[:max_width].ljust(max_width))

    def render(self) -> str:
        rows = ["".join(row).rstrip() for row in self._grid]
        return "\n".join(row.rstrip() for row in rows).rstrip() + "\n"

    def _format_row(self, values: list[str], max_width: int) -> str:
        if not values:
            return ""
        slots = max(1, len(values))
        spacer = 1 if slots > 1 else 0
        cell_width = max(1, (max_width - (spacer * (slots - 1))) // slots)
        cells = [str(value).strip()[:cell_width].ljust(cell_width) for value in values]
        line = (" " * spacer).join(cells)
        return line[:max_width]

    def _write(self, x: int, y: int, text: str) -> None:
        if not (0 <= y < self.height):
            return
        for idx, ch in enumerate(text):
            self._plot(x + idx, y, ch)

    def _plot(self, x: int, y: int, char: str) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return
        if not char:
            return
        self._grid[y][x] = char[0]

    def _clip_rect(self, rect: tuple[int, int, int, int]) -> tuple[int, int, int, int] | None:
        x, y, width, height = rect
        if width <= 0 or height <= 0:
            return None
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width - 1, x + width - 1)
        y1 = min(self.height - 1, y + height - 1)
        if x0 > x1 or y0 > y1:
            return None
        return x0, y0, x1, y1

    def _select_border_chars(self, emphasize: bool) -> dict[str, str]:
        return self.emphasize_chars if emphasize else self.border_chars


@dataclass(slots=True)
class InputModifierState:
    """Current state of input modifiers."""
    ctrl: bool = False
    alt: bool = False
    shift: bool = False
    meta: bool = False


@dataclass(slots=True)
class GuiInputEvent:
    """GUI input event data."""
    event_type: InputEventType
    x: int = 0
    y: int = 0
    key: str | None = None
    char: str | None = None
    button: int | None = None
    modifiers: InputModifierState = field(default_factory=InputModifierState)
    timestamp: float = field(default_factory=time.perf_counter)
    source: str = ""


@dataclass(slots=True)
class InputContext:
    """Context for input event handling."""
    event_bus: EventBus
    window_id: str
    is_active: bool = True
    modifiers: InputModifierState = field(default_factory=InputModifierState)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, hash=False)


@dataclass(slots=True)
class Win32WindowManager:
    """Window manager backed by the native Win32 implementation."""
    window_cls: Any
    availability: Any

    def is_window_available(self) -> bool:
        try:
            return bool(self.availability())
        except Exception:
            return False

    def create_window(self, title: str, width: int, height: int) -> Any:
        return self.window_cls(title, width, height)


@dataclass
class WindowPumpHandle:
    thread: threading.Thread


@dataclass(slots=True)
class TerminalState:
    """Stores terminal state for restoration."""
    fd: int
    original_mode: Any | None
    is_tty: bool


@dataclass(slots=True)
class RenderOutput:
    """Container for rendered output."""
    content: str | bytes
    backend_target: str
    metadata: dict[str, Any] | None = None


@dataclass(slots=True)
class RendererCapabilities:
    """Describes the capabilities of a specific backend."""
    backend_type: BackendTarget
    capabilities: RenderCapability = RenderCapability.NONE
    max_colors: int | None = None
    supports_truecolor: bool = False
    max_layers: int | None = None
    max_width: int | None = None
    max_height: int | None = None
    frame_rate: float | None = None
    custom_metadata: dict[str, Any] = field(default_factory=dict)

    def has_capability(self, capability: RenderCapability) -> bool:
        return bool(self.capabilities & capability)

    def has_all_capabilities(self, *capabilities: RenderCapability) -> bool:
        for cap in capabilities:
            if not self.has_capability(cap):
                return False
        return True

    def has_any_capability(self, *capabilities: RenderCapability) -> bool:
        for cap in capabilities:
            if self.has_capability(cap):
                return True
        return False

    def get_supported_capabilities(self) -> list[RenderCapability]:
        supported: list[RenderCapability] = []
        for cap in RenderCapability:
            if cap != RenderCapability.NONE and self.has_capability(cap):
                supported.append(cap)
        return supported


@dataclass(slots=True)
class LayerTransform:
    """Transformation applied to a layer during composition."""
    offset_x: int = 0
    offset_y: int = 0
    scale_x: float = 1.0
    scale_y: float = 1.0
    opacity: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.opacity <= 1.0:
            raise ValueError(f"Opacity must be between 0.0 and 1.0, got {self.opacity}")
        if self.scale_x <= 0.0 or self.scale_y <= 0.0:
            raise ValueError(f"Scale factors must be positive, got ({self.scale_x}, {self.scale_y})")


@dataclass(slots=True)
class Layer:
    """A compositable rendering layer."""
    name: str
    surface: Surface
    z_index: int = 0
    blend_mode: BlendMode = BlendMode.ALPHA
    transform: LayerTransform | None = None
    visible: bool = True

    def __post_init__(self) -> None:
        if self.transform is None:
            self.transform = LayerTransform()


@dataclass(slots=True)
class FrameTiming:
    """Timing information for a single frame."""
    frame_number: int
    start_time: float
    end_time: float | None = None
    present_time: float | None = None
    target_frame_time: float = 1.0 / 60.0

    @property
    def render_duration(self) -> float | None:
        if self.end_time is None:
            return None
        return self.end_time - self.start_time

    @property
    def total_duration(self) -> float | None:
        if self.present_time is None:
            return None
        return self.present_time - self.start_time

    @property
    def is_late(self) -> bool:
        duration = self.render_duration
        if duration is None:
            return False
        return duration > self.target_frame_time


@dataclass(slots=True)
class Frame:
    """Represents a single rendering frame."""
    frame_number: int
    surface: Surface | None = None
    state: FrameState = FrameState.PENDING
    timing: FrameTiming | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timing is None:
            self.timing = FrameTiming(frame_number=self.frame_number, start_time=time.time())

    def mark_rendering_start(self) -> None:
        self.state = FrameState.RENDERING
        if self.timing:
            self.timing.start_time = time.time()

    def mark_rendering_complete(self) -> None:
        self.state = FrameState.READY
        if self.timing:
            self.timing.end_time = time.time()

    def mark_presented(self) -> None:
        self.state = FrameState.PRESENTED
        if self.timing:
            self.timing.present_time = time.time()

    def mark_dropped(self) -> None:
        self.state = FrameState.DROPPED

    def is_ready_to_present(self) -> bool:
        return self.state == FrameState.READY

    def get_performance_stats(self) -> dict[str, float | None]:
        if self.timing is None:
            return {"render_duration": None, "total_duration": None, "is_late": False}
        return {
            "render_duration": self.timing.render_duration,
            "total_duration": self.timing.total_duration,
            "is_late": self.timing.is_late,
        }


@dataclass(slots=True)
class FrameStats:
    """Statistics for a single frame render."""
    frame_number: int = 0
    layout_time: float = 0.0
    render_time: float = 0.0
    compose_time: float = 0.0
    present_time: float = 0.0
    total_time: float = 0.0
    timestamp: float = 0.0


@dataclass(slots=True)
class PipelineMetrics:
    """Performance metrics for pipeline execution."""
    frames_rendered: int = 0
    frames_dropped: int = 0
    total_layout_time: float = 0.0
    total_render_time: float = 0.0
    total_compose_time: float = 0.0
    total_present_time: float = 0.0
    frame_history: list[FrameStats] = field(default_factory=list)

    @property
    def average_frame_time(self) -> float:
        if self.frames_rendered == 0:
            return 0.0
        total_time = self.total_layout_time + self.total_render_time + self.total_compose_time + self.total_present_time
        return total_time / self.frames_rendered

    @property
    def fps(self) -> float:
        avg_time = self.average_frame_time
        if avg_time == 0.0:
            return 0.0
        return 1.0 / avg_time


@dataclass(slots=True)
class RenderSignal:
    """A rendering event signal."""
    signal_type: SignalType
    data: dict[str, Any]
    timestamp: float
    frame_number: int | None = None


@dataclass(slots=True)
class SurfaceMetadata:
    """Metadata associated with a rendering surface."""
    renderer_type: str
    timestamp: float | None = None
    dirty_regions: list[tuple[int, int, int, int]] | None = None
    custom: dict[str, Any] | None = None


@dataclass(slots=True)
class Surface:
    """Generic rendering surface for holding rendered content."""
    width: int
    height: int
    data: Any | None = None
    metadata: SurfaceMetadata | None = None

    def clear(self) -> None:
        self.data = None
        if self.metadata and self.metadata.dirty_regions:
            self.metadata.dirty_regions.clear()

    def mark_dirty(self, x: int, y: int, width: int, height: int) -> None:
        if self.metadata is None:
            self.metadata = SurfaceMetadata(renderer_type="unknown")
        if self.metadata.dirty_regions is None:
            self.metadata.dirty_regions = []
        self.metadata.dirty_regions.append((x, y, width, height))

    def mark_all_dirty(self) -> None:
        self.mark_dirty(0, 0, self.width, self.height)

    def is_dirty(self) -> bool:
        return bool(self.metadata and self.metadata.dirty_regions)

    def clear_dirty_regions(self) -> None:
        if self.metadata and self.metadata.dirty_regions:
            self.metadata.dirty_regions.clear()

    def resize(self, width: int, height: int) -> None:
        if width != self.width or height != self.height:
            self.width = width
            self.height = height
            self.clear()
            self.mark_all_dirty()


@dataclass(slots=True)
class TextSurface(Surface):
    """Specialized surface for text-based rendering."""
    data: list[str] | None = None

    def __post_init__(self) -> None:
        if self.data is None:
            self.data = [" " * self.width for _ in range(self.height)]

    def set_line(self, y: int, text: str) -> None:
        if self.data is None:
            self.data = [" " * self.width for _ in range(self.height)]
        if 0 <= y < self.height:
            self.data[y] = text[:self.width].ljust(self.width)
            self.mark_dirty(0, y, self.width, 1)

    def get_line(self, y: int) -> str:
        if self.data is None or not (0 <= y < self.height):
            return ""
        return self.data[y]

    def render_to_string(self) -> str:
        if self.data is None:
            return ""
        return "\n".join(self.data)


@dataclass(slots=True)
class PixelSurface(Surface):
    """Specialized surface for pixel-based rendering."""
    data: list[list[tuple[int, int, int, int]]] | None = None

    def __post_init__(self) -> None:
        if self.data is None:
            self.data = [[(0, 0, 0, 0) for _ in range(self.width)] for _ in range(self.height)]

    def set_pixel(self, x: int, y: int, color: tuple[int, int, int, int]) -> None:
        if self.data is None:
            self.__post_init__()
        if self.data and 0 <= x < self.width and 0 <= y < self.height:
            self.data[y][x] = color
            self.mark_dirty(x, y, 1, 1)

    def get_pixel(self, x: int, y: int) -> tuple[int, int, int, int]:
        if self.data is None or not (0 <= x < self.width and 0 <= y < self.height):
            return (0, 0, 0, 0)
        return self.data[y][x]

    def fill(self, color: tuple[int, int, int, int]) -> None:
        if self.data is None:
            self.__post_init__()
        if self.data:
            for y in range(self.height):
                for x in range(self.width):
                    self.data[y][x] = color
        self.mark_all_dirty()


@dataclass(slots=True)
class RenderOptions:
    """Options passed to render pipelines and runtimes."""
    backend: BackendTarget
    renderer_type: RendererType
    width: int | None = None
    height: int | None = None
    vsync: bool = True
    clear_color: Color | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class TerminalInfo:
    """Information about the current terminal environment."""
    terminal_type: TerminalType
    capabilities: set[TerminalCapability]
    width: int
    height: int
    color_support: bool
    unicode_support: bool
    supports_mouse: bool


@dataclass(slots=True, frozen=True)
class CursorPosition:
    """Represents a cursor position on screen."""
    row: int
    col: int

    def __str__(self) -> str:
        return f"({self.row},{self.col})"


@dataclass(slots=True, frozen=True)
class ScreenRegion:
    """Represents a rectangular region on screen."""
    top: int
    left: int
    bottom: int
    right: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    def contains(self, row: int, col: int) -> bool:
        return self.top <= row < self.bottom and self.left <= col < self.right


@dataclass(slots=True, frozen=True)
class ScreenCell:
    """Represents a single character cell on screen."""
    char: str
    style: TextStyle = field(default_factory=TextStyle)
    width: int = 1

    def __post_init__(self) -> None:
        if len(self.char) != 1:
            raise ValueError(f"ScreenCell char must be single character, got {self.char!r}")


@dataclass(slots=True)
class ScreenBuffer:
    """Buffer representing terminal screen contents."""
    width: int
    height: int
    cells: list[list[ScreenCell]] = field(init=False)

    def __post_init__(self) -> None:
        self.cells = []
        for _ in range(self.height):
            row: list[ScreenCell] = []
            for _ in range(self.width):
                row.append(ScreenCell(" "))
            self.cells.append(row)

    def get_cell(self, row: int, col: int) -> ScreenCell:
        if not (0 <= row < self.height and 0 <= col < self.width):
            raise IndexError(f"Position ({row},{col}) out of bounds")
        return self.cells[row][col]

    def set_cell(self, row: int, col: int, cell: ScreenCell) -> None:
        if not (0 <= row < self.height and 0 <= col < self.width):
            raise IndexError(f"Position ({row},{col}) out of bounds")
        self.cells[row][col] = cell

    def clear(self) -> None:
        for row in range(self.height):
            for col in range(self.width):
                self.cells[row][col] = ScreenCell(" ")

    def copy_region(self, src_region: ScreenRegion, dst_row: int, dst_col: int) -> None:
        for src_r in range(src_region.top, src_region.bottom):
            for src_c in range(src_region.left, src_region.right):
                dst_r = dst_row + (src_r - src_region.top)
                dst_c = dst_col + (src_c - src_region.left)
                if 0 <= dst_r < self.height and 0 <= dst_c < self.width:
                    self.cells[dst_r][dst_c] = self.cells[src_r][src_c]


@dataclass(slots=True)
class GuiNode:
    """Renderer-ready representation of a component."""
    component_name: str
    component_id: str | None = None
    key: str | None = None
    name: str | None = None
    kind: ComponentKind = field(default_factory=lambda: ComponentKind.GENERIC)
    variant: str | None = None
    intent: str | None = None
    role: str | None = None
    content: ComponentContent | None = None
    placement: ComponentPlacement | None = None
    accessibility: ComponentAccessibility | None = None
    interactions: InteractionDescriptor | None = None
    render_hints: ComponentRenderHints | None = None
    bindings: list[ComponentDataBinding] = field(default_factory=list)
    states: dict[str, bool] = field(default_factory=dict)
    visible: bool = True
    enabled: bool = True
    focusable: bool = False
    data: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)
    dataset: list[dict[str, Any]] = field(default_factory=list)
    items: list[Any] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    selection: list[int] = field(default_factory=list)
    selection_mode: str | None = None
    sorting: str | None = None
    grouping: str | None = None
    filter_expression: str | None = None
    page_index: int | None = None
    page_size: int | None = None
    total_count: int | None = None
    value: Any | None = None
    secondary_value: Any | None = None
    min_value: float | int | None = None
    max_value: float | int | None = None
    step_value: float | int | None = None
    placeholder_value: Any | None = None
    status: str | None = None
    icon_slot: str | None = None
    badge_text: str | None = None
    tooltip: str | None = None
    animations: list[str] = field(default_factory=list)
    transitions: list[str] = field(default_factory=list)
    text: str | None = None
    children: list[GuiNode] = field(default_factory=list)
    style: ResolvedStyleProtocol | None = None
    layout_style: LayoutStyleProtocol | None = None
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    __weakref__: Any = field(init=False, repr=False)

    @property
    def state(self) -> dict[str, bool]:
        return self.states

    @state.setter
    def state(self, value: dict[str, bool]) -> None:
        self.states = value

    @property
    def metadata(self) -> dict[str, Any]:
        return self.meta

    @metadata.setter
    def metadata(self, value: dict[str, Any]) -> None:
        self.meta = value


@dataclass(frozen=True)
class BackendCapabilities:
    """Capabilities and metadata for a rendering backend."""
    backend_target: BackendTarget
    name: str
    version: str | None = None
    available: bool = True
    priority: int = 0
    supports_gpu: bool = False
    supports_animations: bool = False
    supports_unicode: bool = True
    supports_colors: bool = True
    supports_mouse: bool = False
    supports_keyboard: bool = True
    render_time_ms: float | None = None
    memory_usage_mb: float | None = None
    required_platforms: set[str] = field(default_factory=set)
    excluded_platforms: set[str] = field(default_factory=set)

    @property
    def memory_mb(self) -> float | None:
        return self.memory_usage_mb


@dataclass(slots=True)
class DirtyRegion:
    """Represents a region that needs to be updated."""
    x: int
    y: int
    width: int
    height: int
    priority: int = 0
    layer_index: int = 0


@dataclass(slots=True)
class RenderBatch:
    """A batch of dirty regions to be rendered together."""
    regions: list[DirtyRegion] = field(default_factory=list)
    timestamp: float = 0.0

    def add_region(self, region: DirtyRegion) -> None:
        self.regions.append(region)

    def get_bounding_box(self) -> tuple[int, int, int, int] | None:
        if not self.regions:
            return None
        min_x = min(r.x for r in self.regions)
        min_y = min(r.y for r in self.regions)
        max_x = max(r.x + r.width for r in self.regions)
        max_y = max(r.y + r.height for r in self.regions)
        return (min_x, min_y, max_x - min_x, max_y - min_y)

    def coalesce_regions(self, max_regions: int = 10) -> list[tuple[int, int, int, int]]:
        if len(self.regions) <= max_regions:
            return [(r.x, r.y, r.width, r.height) for r in self.regions]
        sorted_regions = sorted(self.regions, key=lambda r: r.priority, reverse=True)
        coalesced: list[tuple[int, int, int, int]] = []
        for region in sorted_regions:
            merged = False
            for i, (x, y, w, h) in enumerate(coalesced):
                if (region.x < x + w and region.x + region.width > x and
                    region.y < y + h and region.y + region.height > y):
                    new_x = min(x, region.x)
                    new_y = min(y, region.y)
                    new_w = max(x + w, region.x + region.width) - new_x
                    new_h = max(y + h, region.y + region.height) - new_y
                    coalesced[i] = (new_x, new_y, new_w, new_h)
                    merged = True
                    break
            if not merged:
                coalesced.append((region.x, region.y, region.width, region.height))
        return coalesced[:max_regions]


@dataclass(slots=True)
class Rect:
    """Axis-aligned rectangle."""
    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    def contains(self, px: float, py: float) -> bool:
        return self.x <= px <= self.right and self.y <= py <= self.bottom

    def intersects(self, other: Rect) -> bool:
        return not (
            other.x > self.right
            or other.right < self.x
            or other.y > self.bottom
            or other.bottom < self.y
        )

    def intersection(self, other: Rect) -> Rect | None:
        left = max(self.x, other.x)
        top = max(self.y, other.y)
        right = min(self.right, other.right)
        bottom = min(self.bottom, other.bottom)
        if right <= left or bottom <= top:
            return None
        return Rect(left, top, right - left, bottom - top)

    def union(self, other: Rect) -> Rect:
        left = min(self.x, other.x)
        top = min(self.y, other.y)
        right = max(self.right, other.right)
        bottom = max(self.bottom, other.bottom)
        return Rect(left, top, right - left, bottom - top)

    def translate(self, dx: float, dy: float) -> Rect:
        return Rect(self.x + dx, self.y + dy, self.width, self.height)


@dataclass(slots=True)
class Transform:
    """2D affine transform matrix."""
    m11: float = 1.0
    m12: float = 0.0
    m21: float = 0.0
    m22: float = 1.0
    dx: float = 0.0
    dy: float = 0.0

    def copy(self) -> Transform:
        return Transform(self.m11, self.m12, self.m21, self.m22, self.dx, self.dy)

    def multiply(self, other: Transform) -> Transform:
        return Transform(
            m11=self.m11 * other.m11 + self.m12 * other.m21,
            m12=self.m11 * other.m12 + self.m12 * other.m22,
            m21=self.m21 * other.m11 + self.m22 * other.m21,
            m22=self.m21 * other.m12 + self.m22 * other.m22,
            dx=self.m11 * other.dx + self.m12 * other.dy + self.dx,
            dy=self.m21 * other.dx + self.m22 * other.dy + self.dy,
        )

    def translate(self, dx: float, dy: float) -> None:
        self.dx += dx
        self.dy += dy

    def scale(self, sx: float, sy: float) -> None:
        self.m11 *= sx
        self.m22 *= sy

    def rotate(self, degrees: float) -> None:
        radians = math.radians(degrees)
        cos_v = math.cos(radians)
        sin_v = math.sin(radians)
        rotation = Transform(m11=cos_v, m12=-sin_v, m21=sin_v, m22=cos_v)
        rotated = self.multiply(rotation)
        self.m11, self.m12, self.m21, self.m22 = rotated.m11, rotated.m12, rotated.m21, rotated.m22
        self.dx, self.dy = rotated.dx, rotated.dy

    def apply(self, x: float, y: float) -> tuple[float, float]:
        return (
            self.m11 * x + self.m12 * y + self.dx,
            self.m21 * x + self.m22 * y + self.dy,
        )

__all__ = [
    "BackendCapabilities",
    "CursorPosition",
    "DirtyRegion",
    "Frame",
    "FrameStats",
    "FrameTiming",
    "GuiInputEvent",
    "GuiNode",
    "InputContext",
    "InputModifierState",
    "Layer",
    "LayerTransform",
    "PipelineMetrics",
    "PixelSurface",
    "Rect",
    "RenderBatch",
    "RendererCapabilities",
    "RenderOptions",
    "RenderOutput",
    "RenderSignal",
    "ScreenBuffer",
    "ScreenCell",
    "ScreenRegion",
    "Surface",
    "SurfaceMetadata",
    "TerminalInfo",
    "TerminalState",
    "TextSurface",
    "Transform",
    "UnicodeCanvas",
    "WindowPumpHandle",
    "Win32WindowManager",
]