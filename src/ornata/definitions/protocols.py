"""All Protocol definitions for Ornata. """

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from ornata.definitions.dataclasses.components import Component
    from ornata.definitions.dataclasses.events import Event
    from ornata.definitions.dataclasses.kernel import BackendCapabilities, KernelConfig, KernelState, PluginMetadata, SubsystemInfo
    from ornata.definitions.dataclasses.layout import Bounds, LayoutResult
    from ornata.definitions.dataclasses.vdom import VDOMNode
    from ornata.definitions.enums import BackendTarget

class PlatformEventHandler(Protocol):
    def is_available(self) -> bool: ...
    def start_event_loop(self) -> None: ...
    def stop_event_loop(self) -> None: ...
    def poll_events(self) -> Iterator[Event]: ...


class RenderCallback(Protocol):
    def __call__(self, rectangles: list[tuple[int, int, int, int]]) -> None: ...


class Canvas(Protocol):
    viewport_w: int
    viewport_h: int

    def save(self) -> None: ...
    def restore(self) -> None: ...
    def fill_rect(self, x: int, y: int, w: int, h: int, color: tuple[int, int, int, int]) -> None: ...
    def stroke_rect(self, x: int, y: int, w: int, h: int, color: tuple[int, int, int, int], width: int) -> None: ...
    def draw_text(
        self,
        x: int,
        y: int,
        text: str,
        color: tuple[int, int, int, int],
        font_face: str | None,
        px: int,
        weight: int | str | None,
    ) -> None: ...


class GuiNodeLike(Protocol):
    component_name: str
    text: str | None
    children: list[GuiNodeLike]
    style: Any | None
    metadata: dict[str, Any]
    x: int
    y: int
    width: int
    height: int


class WindowManagerProtocol(Protocol):
    def is_window_available(self) -> bool: ...
    def create_window(self, title: str, width: int, height: int) -> Any: ...


class MeasureProtocol(Protocol):
    width: int
    height: int
    @classmethod
    def from_text(cls, text: str) -> MeasureProtocol: ...


class RenderableProtocol(Protocol):
    def render(self) -> str | Iterable[str] | None: ...


class LayoutAlgorithm(Protocol):
    def calculate(
        self,
        component: Component,
        container_bounds: Bounds,
        backend_target: BackendTarget,
    ) -> LayoutResult: ...


class LayoutConstraint(Protocol):
    def validate(self, component: Component, bounds: Bounds) -> bool: ...
    def apply(self, component: Component, bounds: Bounds) -> Bounds: ...


class ResponsiveBreakpoint(Protocol):
    @property
    def min_width(self) -> int | None: ...
    @property
    def max_width(self) -> int | None: ...
    @property
    def min_height(self) -> int | None: ...
    @property
    def max_height(self) -> int | None: ...


class LayoutCacheKey(Protocol):
    def __hash__(self) -> int: ...
    def __eq__(self, other: Any) -> bool: ...


class LayoutStyleProtocol(Protocol): ...
class ResolvedStyleProtocol(Protocol): ...


class BootstrapPhase(Protocol):
    def get_name(self) -> str: ...
    def get_dependencies(self) -> set[str]: ...
    def execute(self, state: KernelState) -> KernelState: ...


class ConfigLoader(Protocol):
    def load_config(self, search_paths: list[str]) -> dict[str, Any]: ...
    def merge_configs(
        self,
        base_config: dict[str, Any],
        override_config: dict[str, Any],
    ) -> dict[str, Any]: ...


class BackendSelector(Protocol):
    def select_backend(
        self,
        available_backends: dict[BackendTarget, BackendCapabilities],
        config: KernelConfig,
    ) -> BackendTarget: ...
    def get_fallback_chain(
        self,
        primary_backend: BackendTarget,
        available_backends: dict[BackendTarget, BackendCapabilities],
    ) -> list[BackendTarget]: ...


class PluginLoader(Protocol):
    def discover_plugins(self, search_paths: list[str]) -> list[PluginMetadata]: ...
    def load_plugin(self, metadata: PluginMetadata) -> Any: ...
    def validate_plugin(self, plugin: Any, metadata: PluginMetadata) -> bool: ...


class SubsystemRegistry(Protocol):
    def register_subsystem(self, name: str, info: SubsystemInfo) -> None: ...
    def unregister_subsystem(self, name: str) -> None: ...
    def get_subsystem(self, name: str) -> SubsystemInfo | None: ...
    def get_subsystems_by_status(self, status: str) -> list[SubsystemInfo]: ...
    def check_dependencies(self, subsystem_name: str) -> bool: ...


class ComponentFactory(Protocol):
    def __call__(self, props: dict[str, Any] | None = None) -> Component: ...


@runtime_checkable
class HostObjectProtocol(Protocol):
    @property
    def vdom_key(self) -> str: ...
    @property
    def component_name(self) -> str: ...
    @property
    def backend_target(self) -> BackendTarget: ...
    def initialize(self, vdom_node: VDOMNode) -> None: ...
    def update_properties(self, properties: dict[str, Any]) -> None: ...
    def destroy(self) -> None: ...
    @property
    def is_active(self) -> bool: ...
    def set_active(self, active: bool) -> None: ...
    @property
    def properties(self) -> dict[str, Any]: ...
    def get_property(self, key: str, default: Any = None) -> Any: ...
    def set_property(self, key: str, value: Any) -> None: ...
    def handle_event(self, event_type: str, event_data: dict[str, Any]) -> bool: ...
    def add_event_handler(self, event_type: str, handler: Any) -> None: ...
    def remove_event_handler(self, event_type: str, handler: Any) -> None: ...
    def get_debug_info(self) -> dict[str, Any]: ...
    def clone(self) -> HostObjectProtocol: ...


__all__ = [
    "PlatformEventHandler",
    "RenderCallback",
    "Canvas",
    "GuiNodeLike",
    "WindowManagerProtocol",
    "MeasureProtocol",
    "LayoutAlgorithm",
    "LayoutConstraint",
    "ResponsiveBreakpoint",
    "LayoutCacheKey",
    "LayoutStyleProtocol",
    "ResolvedStyleProtocol",
    "BootstrapPhase",
    "ConfigLoader",
    "BackendSelector",
    "PluginLoader",
    "SubsystemRegistry",
    "HostObjectProtocol",
    "ComponentFactory",
]