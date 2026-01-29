""" TEMPORARY FILE FOR GPU METHODS THAT NEED TO BE MOVED APPROPRIATELY """

from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from ornata.definitions.constants import ZERO_TIME
from ornata.definitions.dataclasses.components import ComponentKind
from ornata.definitions.dataclasses.events import Event, EventPriority, EventType
from ornata.definitions.dataclasses.rendering import GuiNode, Rect, Transform
from ornata.definitions.dataclasses.styling import Color, Font

if TYPE_CHECKING:
    from ornata.definitions.dataclasses.components import Component
    from ornata.definitions.dataclasses.gpu import CompositorLayer, Geometry
    from ornata.definitions.dataclasses.layout import LayoutStyle
    from ornata.definitions.dataclasses.rendering import DirtyRegion
    from ornata.definitions.dataclasses.styling import ResolvedStyle


class GPUResource(ABC):
    """Base class for GPU-backed resources such as textures and buffers."""

    __slots__ = ("_valid",)

    def __init__(self) -> None:
        self._valid = True

    @property
    def valid(self) -> bool:
        return self._valid

    @abstractmethod
    def destroy(self) -> None:
        self._valid = False


class Shader(GPUResource):
    """Cross-platform shader abstraction shared by all backends."""

    def __init__(self, name: str, vertex_source: str, fragment_source: str) -> None:
        super().__init__()
        self.name = name
        self.vertex_source = vertex_source
        self.fragment_source = fragment_source
        self.compiled = False
        self.program: Any | None = None
        self.backend: GPUBackend | None = None
        self.uniform_values: dict[str, float | int | list[float] | list[int]] = {}

    def compile(self, backend: GPUBackend) -> bool:
        try:
            compiled_shader = backend.create_shader(self.name, self.vertex_source, self.fragment_source)
            if compiled_shader is not None:
                self.program = getattr(compiled_shader, "_program", compiled_shader)
                self.backend = backend
                self.compiled = True
                return True
            return False
        except Exception:
            self.compiled = False
            return False

    def bind(self) -> None:
        from ornata.api.exports.definitions import GPUShaderCompilationError

        if not self.compiled:
            raise GPUShaderCompilationError(f"Shader {self.name} is not compiled")
        if self.backend is None:
            raise GPUShaderCompilationError(f"Shader {self.name} has no associated backend")

    def set_uniform(self, name: str, value: float | int | list[float] | list[int]) -> None:
        from ornata.api.exports.definitions import GPUShaderCompilationError

        if not self.compiled:
            raise GPUShaderCompilationError(f"Shader {self.name} is not compiled")
        if self.backend is None:
            raise GPUShaderCompilationError(f"Shader {self.name} has no associated backend")

        self.uniform_values[name] = value

        backend_handler = getattr(self.backend, "set_uniform", None)
        if callable(backend_handler):
            backend_handler(self, name, value)
            return

        program_uniform_setter = getattr(self.program, "set_uniform", None)
        if callable(program_uniform_setter):
            program_uniform_setter(name, value)

    def destroy(self) -> None:
        program_cleanup = getattr(self.program, "destroy", None)
        if callable(program_cleanup):
            program_cleanup()
        self.program = None
        self.backend = None
        self.uniform_values.clear()
        self.compiled = False
        super().destroy()


class Texture(GPUResource):
    """Simple texture wrapper shared across the rendering stack."""

    __slots__ = ("width", "height", "format_name", "_native_handle")

    def __init__(self, width: int, height: int, format_name: str = "rgba8") -> None:
        super().__init__()
        self.width = width
        self.height = height
        self.format_name = format_name
        self._native_handle: Any | None = None

    def destroy(self) -> None:
        super().destroy()
        self._native_handle = None


class Buffer(GPUResource):
    """Generic GPU buffer representation."""

    __slots__ = ("size_bytes", "usage", "_native_handle")

    def __init__(self, size_bytes: int, usage: str = "vertex") -> None:
        super().__init__()
        self.size_bytes = size_bytes
        self.usage = usage
        self._native_handle: Any | None = None

    def destroy(self) -> None:
        super().destroy()
        self._native_handle = None


class RenderTarget:
    """Render target consisting of colour and optional depth textures."""

    __slots__ = ("width", "height", "color_texture", "depth_texture")

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.color_texture: Texture | None = None
        self.depth_texture: Texture | None = None


class GPUBackend(ABC):
    """Abstract base class for GPU backends."""

    shaders_: dict[str, Shader] = {}

    vertex_buffer_manager: Any | None = None
    index_buffer_manager: Any | None = None
    hardware_buffer_manager: Any | None = None
    buffers: Any | None = None

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def create_shader(self, name: str, vertex_src: str, fragment_src: str) -> Shader | None:
        raise NotImplementedError

    @abstractmethod
    def render_geometry(self, geometry: Geometry, shader: Shader) -> None:
        raise NotImplementedError

    @abstractmethod
    def render_instanced_geometry(
        self,
        geometry: Geometry,
        instance_data: list[float],
        instance_count: int,
        shader: Shader,
    ) -> None:
        raise NotImplementedError

    def create_vertex_buffer(self, data: list[float], usage: str = "static") -> Any:
        raise NotImplementedError

    def create_index_buffer(self, data: list[int], usage: str = "static") -> Any:
        raise NotImplementedError

    def create_buffer(self, data: list[int] | list[float], buffer_type: str, usage: str = "static") -> Any:
        raise NotImplementedError

    def update_vertex_buffer(self, buffer: Any, data: list[float]) -> None:
        raise NotImplementedError

    def update_index_buffer(self, buffer: Any, data: list[int]) -> None:
        raise NotImplementedError

    @abstractmethod
    def upload_to_gpu(self, buffer: bytearray, size: int) -> None:
        """Upload data from CPU staging memory into GPU-accessible memory."""
        raise NotImplementedError

    @abstractmethod
    def download_from_gpu(self, buffer: bytearray, size: int) -> int:
        """Download data from GPU memory into the provided staging buffer."""
        raise NotImplementedError

    @abstractmethod
    def compile_vertex_shader(self, source: str) -> Any: ...
    @abstractmethod
    def compile_fragment_shader(self, source: str) -> Any: ...
    @abstractmethod
    def compile_geometry_shader(self, source: str) -> Any: ...
    @abstractmethod
    def compile_mesh_shader(self, source: str) -> Any: ...
    @abstractmethod
    def compile_task_shader(self, source: str) -> Any: ...
    @abstractmethod
    def compile_tess_control_shader(self, source: str) -> Any: ...
    @abstractmethod
    def compile_tess_eval_shader(self, source: str) -> Any: ...
    @abstractmethod
    def compile_compute_shader(self, source: str) -> Any: ...
    @abstractmethod
    def compile_raygen_shader(self, source: str) -> Any: ...
    @abstractmethod
    def compile_miss_shader(self, source: str) -> Any: ...
    @abstractmethod
    def compile_closesthit_shader(self, source: str) -> Any: ...

    @abstractmethod
    def create_tessellation_pipeline(
        self,
        name: str,
        vs_src: str,
        tcs_src: str,
        tes_src: str,
        fs_src: str,
    ) -> Shader:
        raise NotImplementedError

    @abstractmethod
    def create_mesh_pipeline(
        self,
        name: str,
        task_src: str | None,
        mesh_src: str,
        fs_src: str,
    ) -> Shader:
        raise NotImplementedError

    @abstractmethod
    def create_compute(self, name: str, cs_src: str) -> Shader:
        raise NotImplementedError

    @abstractmethod
    def create_raytracing_pipeline(
        self,
        name: str,
        rgen_src: str,
        rmiss_src: str,
        rchit_src: str,
        anyhit_src: str | None,
    ) -> Shader:
        raise NotImplementedError

    @property
    def shaders(self) -> dict[str, Shader]:
        return self.shaders_

    def link_program(self, vertex_shader: Shader, fragment_shader: Shader) -> Any | None:
        raise NotImplementedError

    @property
    def device(self) -> Any | None:
        """Expose the underlying device handle if available."""
        return None

    @property
    def context(self) -> Any | None:
        """Expose the underlying device context when available."""
        return None

    def get_capabilities(self) -> dict[str, bool | int]:
        """Return backend-reported capability flags."""
        return {}

    def get_limits(self) -> dict[str, int]:
        """Return backend-reported hardware limits."""
        return {}

    def evict_memory_block(self, block_id: str) -> bool:
        """Evict a residency block if the backend supports it."""
        return False

    def restore_memory_block(self, block_id: str) -> bool:
        """Restore a residency block if the backend supports it."""
        return False

    def dispose_shader(self, shader: Shader) -> None:
        """Dispose of backend-specific shader resources (optional)."""
        # Default is no-op for backends that don't track resources.
        return None

    def shutdown(self) -> None:
        """Shutdown the backend cleanly (optional)."""
        # Default is no-op for stateless backends.
        return None


class GPUContext(ABC):
    """Abstract interface implemented by every GPU context."""

    def __init__(self) -> None:
        self.current_render_target: RenderTarget | None = None

    @abstractmethod
    def make_current(self) -> None: ...

    @abstractmethod
    def present(self) -> None: ...

    @abstractmethod
    def create_texture(self, width: int, height: int, format_name: str = "rgba8") -> Texture: ...

    @abstractmethod
    def create_buffer(self, size_bytes: int, usage: str = "vertex") -> Buffer: ...

    @abstractmethod
    def create_shader(self, source: str, shader_type: str = "vertex") -> Shader: ...

    @abstractmethod
    def set_render_target(self, target: RenderTarget | None) -> None: ...

    @abstractmethod
    def clear(self, color: Color) -> None: ...

    @abstractmethod
    def draw_rect(self, rect: Rect, color: Color) -> None: ...

    @abstractmethod
    def draw_textured_rect(self, rect: Rect, texture: Texture) -> None: ...

    @abstractmethod
    def draw_text(self, text: str, position: tuple[float, float], font: Font, color: Color) -> None: ...


# ---------------------------------------------------------------------------
# GUI / compositor types
# ---------------------------------------------------------------------------

class CompositorBase:
    """Minimal compositor base class shared by CLI and GUI renderers."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.layers: list[CompositorLayer] = []
        self.dirty_regions: list[DirtyRegion] = []
        self.output_texture: Texture | None = None

    def resize(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.output_texture = None

    def add_layer(self, layer: CompositorLayer) -> None:
        self.layers.append(layer)
        self.layers.sort(key=lambda item: item.z_index)

    def remove_layer(self, layer: CompositorLayer) -> None:
        if layer in self.layers:
            self.layers.remove(layer)

    def mark_dirty(self, region: DirtyRegion) -> None:
        self.dirty_regions.append(region)

    def clear_dirty_regions(self) -> None:
        self.dirty_regions.clear()

    def composite(self, context: GPUContext) -> Texture:
        if self.output_texture is None:
            self.output_texture = context.create_texture(self.width, self.height)
        target = RenderTarget(self.width, self.height)
        target.color_texture = self.output_texture
        context.set_render_target(target)
        context.clear(Color(0, 0, 0, 0))
        for layer in self.layers:
            if not layer.visible or layer.opacity <= 0:
                continue
            context.draw_textured_rect(layer.rect, layer.texture)
        return self.output_texture


class PlatformWindow(ABC):
    """Abstract base class describing platform windows."""

    def __init__(self, title: str, width: int, height: int) -> None:
        self.title = title
        self.width = width
        self.height = height
        self._native_handle: Any = None
        self._gpu_context: GPUContext | None = None

    @property
    @abstractmethod
    def handle(self) -> Any: ...

    @abstractmethod
    def show(self) -> None: ...

    @abstractmethod
    def hide(self) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

    @abstractmethod
    def set_title(self, title: str) -> None: ...

    @abstractmethod
    def resize(self, width: int, height: int) -> None: ...

    @abstractmethod
    def get_gpu_context(self) -> GPUContext | None: ...

    @abstractmethod
    def render_gui_node(self, node: GuiNode) -> None: ...


class Canvas:
    """Immediate-mode drawing canvas with transform + clipping support."""

    def __init__(self, context: GPUContext, width: int, height: int) -> None:
        self.context = context
        self.viewport_w = width
        self.viewport_h = height
        self._transform_stack: list[Transform] = [Transform()]
        self._clip_stack: list[Rect | None] = [None]

    @property
    def current_transform(self) -> Transform:
        return self._transform_stack[-1]

    @property
    def current_clip(self) -> Rect | None:
        return self._clip_stack[-1]

    def save(self) -> None:
        self._transform_stack.append(self.current_transform.copy())
        current = self.current_clip
        self._clip_stack.append(copy.deepcopy(current) if current else None)

    def restore(self) -> None:
        if len(self._transform_stack) > 1:
            self._transform_stack.pop()
        if len(self._clip_stack) > 1:
            self._clip_stack.pop()

    def translate(self, x: float, y: float) -> None:
        self.current_transform.translate(x, y)

    def scale(self, sx: float, sy: float) -> None:
        self.current_transform.scale(sx, sy)

    def rotate(self, angle: float) -> None:
        self.current_transform.rotate(angle)

    def clip_rect(self, rect: Rect) -> None:
        x1, y1 = self.current_transform.apply(rect.x, rect.y)
        x2, y2 = self.current_transform.apply(rect.right, rect.bottom)
        world = Rect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))

        existing = self.current_clip
        if existing is None:
            self._clip_stack[-1] = world
        else:
            inter = existing.intersection(world)
            self._clip_stack[-1] = inter

    def _apply_clip(self, x: float, y: float, w: float, h: float) -> Rect | None:
        if w <= 0 or h <= 0:
            return None

        clip = self.current_clip
        if clip is None:
            return Rect(x, y, w, h)
        rect = Rect(x, y, w, h)
        return clip.intersection(rect)

    def fill_rect(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        color: tuple[int, int, int, int],
    ) -> None:
        x1, y1 = self.current_transform.apply(x, y)
        clipped = self._apply_clip(x1, y1, w, h)
        if clipped is None:
            return
        gpu_color = Color.from_rgba_bytes(*color)
        self.context.draw_rect(clipped, gpu_color)

    def stroke_rect(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        color: tuple[int, int, int, int],
        width: int,
    ) -> None:
        self.fill_rect(x, y, w, width, color)
        self.fill_rect(x, y + h - width, w, width, color)
        self.fill_rect(x, y, width, h, color)
        self.fill_rect(x + w - width, y, width, h, color)

    def draw_text(
        self,
        x: int,
        y: int,
        text: str,
        color: tuple[int, int, int, int],
        font_face: str | None,
        px: int,
        weight: int | str | None,
    ) -> None:
        gpu_color = Color.from_rgba_bytes(*color)
        font = Font(family=font_face or "Arial", size=float(px), weight=weight or 400)
        tx, ty = self.current_transform.apply(x, y)
        self.context.draw_text(text, (float(tx), float(ty)), font, gpu_color)

def create_event_fast(event_type: EventType | None = None, data: Any | None = None) -> Event:
    """Create event with minimal overhead for the hot path."""
    return Event(
        type=event_type or EventType.TICK,
        data=data,
        priority=EventPriority.NORMAL,
        timestamp=ZERO_TIME,
    )

def component_to_gui_node(
    component: Component,
    *,
    style: ResolvedStyle | None = None,
    layout_style: LayoutStyle | None = None,
    children: list[GuiNode] | None = None,
) -> GuiNode:
    """Create a GuiNode snapshot from a Component."""

    states = dict(getattr(component, "states", {}))
    data = dict(getattr(component, "data", {}))
    meta = dict(getattr(component, "meta", {}))
    dataset = [dict(row) for row in getattr(component, "dataset", [])]
    items = list(getattr(component, "items", []))
    columns = list(getattr(component, "columns", []))
    rows = [list(r) for r in getattr(component, "rows", [])]
    selection = list(getattr(component, "selection", []))
    animations = list(getattr(component, "animations", []))
    transitions = list(getattr(component, "transitions", []))
    bindings = list(getattr(component, "bindings", []))

    if children is None:
        children = [component_to_gui_node(child) for child in getattr(component, "children", [])]

    comp_name = getattr(component, "component_name", None) or type(component).__name__
    text_value: str | None = None
    content = getattr(component, "content", None)
    if content is not None:
        text_value = (
            getattr(content, "text", None)
            or getattr(content, "body", None)
            or getattr(content, "title", None)
            or getattr(content, "subtitle", None)
        )

    return GuiNode(
        component_name=comp_name,
        component_id=getattr(component, "component_id", None),
        key=getattr(component, "key", None),
        name=getattr(component, "name", None),
        kind=getattr(component, "kind", ComponentKind.GENERIC),
        variant=getattr(component, "variant", None),
        intent=getattr(component, "intent", None),
        role=getattr(component, "role", None),
        content=content,
        placement=getattr(component, "placement", None),
        accessibility=getattr(component, "accessibility", None),
        interactions=getattr(component, "interactions", None),
        render_hints=getattr(component, "render_hints", None),
        bindings=bindings,
        states=states,
        visible=getattr(component, "visible", True),
        enabled=getattr(component, "enabled", True),
        focusable=getattr(component, "focusable", False),
        data=data,
        meta=meta,
        dataset=dataset,
        items=items,
        columns=columns,
        rows=rows,
        selection=selection,
        selection_mode=getattr(component, "selection_mode", None),
        sorting=getattr(component, "sorting", None),
        grouping=getattr(component, "grouping", None),
        filter_expression=getattr(component, "filter_expression", None),
        page_index=getattr(component, "page_index", None),
        page_size=getattr(component, "page_size", None),
        total_count=getattr(component, "total_count", None),
        value=getattr(component, "value", None),
        secondary_value=getattr(component, "secondary_value", None),
        min_value=getattr(component, "min_value", None),
        max_value=getattr(component, "max_value", None),
        step_value=getattr(component, "step_value", None),
        placeholder_value=getattr(component, "placeholder_value", None),
        status=getattr(component, "status", None),
        icon_slot=getattr(component, "icon_slot", None),
        badge_text=getattr(component, "badge_text", None),
        tooltip=getattr(component, "tooltip", None),
        animations=animations,
        transitions=transitions,
        text=text_value,
        children=children,
        style=style,
        layout_style=layout_style,
    )

__all__ = [
    "GPUResource",
    "Shader",
    "Texture",
    "Buffer",
    "RenderTarget",
    "GPUBackend",
    "GPUContext",
    "CompositorBase",
    "PlatformWindow",
    "Canvas",
    "create_event_fast",
    "component_to_gui_node",
]