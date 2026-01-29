""" Components Dataclasses for Ornata """

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ornata.definitions.enums import Alignment, ComponentKind, InteractionType

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from ornata.definitions.dataclasses.layout import LayoutStyle
    from ornata.definitions.dataclasses.styling import Property, Span
    from ornata.definitions.protocols import ComponentFactory

# Forward declaration for recursive type hints
ComponentEventHandler = Any 

@dataclass(slots=True, frozen=True)
class StateBlock:
    """Component block optionally restricted to states."""
    states: frozenset[str]
    properties: list[Property]
    span: Span
    raw_props: list[tuple[str, str]] | None = None

    def matches(self, active_states: frozenset[str]) -> bool:
        """Return ``True`` when this block applies to ``active_states``."""
        if not self.states or self.states == frozenset({"default"}):
            return True
        return self.states.issubset(active_states)


@dataclass(slots=True, frozen=True)
class ComponentRule:
    """Collection of state blocks for a component selector."""
    component: str
    blocks: list[StateBlock]
    span: Span


@dataclass(slots=True)
class ComponentPlacement:
    """Absolute or logical placement for a component."""
    x: float | None = None
    y: float | None = None
    z_index: int | None = None
    layer: str | None = None
    row: int | None = None
    column: int | None = None
    order: int | None = None
    anchor: Alignment | None = None
    rotation: float | None = None
    scale_x: float | None = None
    scale_y: float | None = None


@dataclass(slots=True)
class ComponentContent:
    """Rich content channels exposed by a component."""
    title: str | None = None
    subtitle: str | None = None
    heading: str | None = None
    subheading: str | None = None
    text: str | None = None
    body: str | None = None
    paragraphs: list[str] = field(default_factory=list)
    caption: str | None = None
    tooltip: str | None = None
    status_text: str | None = None
    placeholder: str | None = None
    prefix: str | None = None
    suffix: str | None = None
    icon: str | None = None
    icon_alt: str | None = None
    media_source: str | None = None
    media_alt: str | None = None
    thumbnail_source: str | None = None
    actions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ComponentDataBinding:
    """Declarative binding between UI state and data sources."""
    source: str | None = None
    path: str | None = None
    formatter: str | None = None
    parser: str | None = None
    locale: str | None = None
    is_two_way: bool = False


@dataclass(slots=True)
class ComponentAccessibility:
    """Accessibility metadata promoted to renderers."""
    label: str | None = None
    description: str | None = None
    role: str | None = None
    hint: str | None = None
    language: str | None = None
    live_region: str | None = None
    tab_index: int | None = None
    shortcut: str | None = None
    announces: bool = False
    is_modal: bool = False


@dataclass(slots=True)
class InteractionDescriptor:
    """Describes how a component should respond to inputs."""
    types: frozenset[InteractionType] = field(default_factory=frozenset)
    debounce_ms: int | None = None
    repeat_interval_ms: int | None = None
    cursor: str | None = None
    is_toggle: bool = False
    accelerator: str | None = None


@dataclass(slots=True)
class ComponentRenderHints:
    """Renderer-specific hints for scheduling and composition."""
    layer: str | None = None
    priority: int | None = None
    cacheable: bool = False
    prefers_gpu: bool = False
    prefers_text_engine: bool = False
    offscreen: bool = False
    rtl: bool = False
    hydration_key: str | None = None


@dataclass(slots=True)
class ComponentMeasurement:
    """Simple measurement container used by layout/rendering systems."""
    width: float = 0.0
    height: float = 0.0


@dataclass(frozen=True)
class ComponentVersion:
    """Semantic version information for a component."""
    major: int
    minor: int
    patch: int
    prerelease: str | None = None
    build: str | None = None

    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version

    @classmethod
    def parse(cls, version_str: str) -> ComponentVersion:
        import re
        match = re.match(
            r"^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?(?:\+([a-zA-Z0-9.-]+))?$",
            version_str,
        )
        if not match:
            raise ValueError(f"Invalid version format: {version_str}")
        major, minor, patch, prerelease, build = match.groups()
        return cls(
            major=int(major),
            minor=int(minor),
            patch=int(patch),
            prerelease=prerelease,
            build=build,
        )

    def _as_tuple(self) -> tuple[int, int, int, str | None, str | None]:
        """Return a tuple representation for rich comparison operations.

        Returns:
            Tuple of major, minor, patch, prerelease, and build components.
        """
        return (self.major, self.minor, self.patch, self.prerelease, self.build)

    def __lt__(self, other: object) -> bool:
        """Return True if this version is less than other.

        Args:
            other: Object to compare against.

        Returns:
            True if other is a ComponentVersion and this instance is less than it.
        """
        if not isinstance(other, ComponentVersion):
            return NotImplemented
        return self._as_tuple() < other._as_tuple()

    def __le__(self, other: object) -> bool:
        """Return True if this version is less than or equal to other.

        Args:
            other: Object to compare against.

        Returns:
            True if other is a ComponentVersion and this instance is less than or equal to it.
        """
        if not isinstance(other, ComponentVersion):
            return NotImplemented
        return self._as_tuple() <= other._as_tuple()

    def __gt__(self, other: object) -> bool:
        """Return True if this version is greater than other.

        Args:
            other: Object to compare against.

        Returns:
            True if other is a ComponentVersion and this instance is greater than it.
        """
        if not isinstance(other, ComponentVersion):
            return NotImplemented
        return self._as_tuple() > other._as_tuple()

    def __ge__(self, other: object) -> bool:
        """Return True if this version is greater than or equal to other.

        Args:
            other: Object to compare against.

        Returns:
            True if other is a ComponentVersion and this instance is greater than or equal to it.
        """
        if not isinstance(other, ComponentVersion):
            return NotImplemented
        return self._as_tuple() >= other._as_tuple()


@dataclass(frozen=True)
class VersionConstraint:
    """Version constraint for component compatibility."""
    minimum_version: ComponentVersion | None = None
    maximum_version: ComponentVersion | None = None
    exact_version: ComponentVersion | None = None
    exclude_versions: set[ComponentVersion] = field(default_factory=set)

    def is_satisfied_by(self, version: ComponentVersion) -> bool:
        if self.exact_version:
            return version == self.exact_version
        if version in self.exclude_versions:
            return False
        if self.minimum_version and version < self.minimum_version:
            return False
        if self.maximum_version and version > self.maximum_version:
            return False
        return True


@dataclass(slots=True)
class ComponentInfo:
    """Public metadata describing a registered component factory."""
    name: str
    factory: ComponentFactory
    version: ComponentVersion | None = None
    description: str | None = None
    category: str | None = None
    kind: ComponentKind = field(default_factory=lambda: ComponentKind.GENERIC)
    keywords: frozenset[str] = frozenset()
    supports_children: bool = True
    defaults: dict[str, Any] = field(default_factory=dict)


@dataclass
class Component:
    """Describes the full set of options shared by all components."""
    component_name: str | None = None
    component_id: str | None = None
    key: str | None = None
    name: str | None = None
    kind: ComponentKind = ComponentKind.GENERIC
    variant: str | None = None
    intent: str | None = None
    role: str | None = None
    content: ComponentContent = field(default_factory=ComponentContent)
    placement: ComponentPlacement = field(default_factory=ComponentPlacement)
    accessibility: ComponentAccessibility = field(default_factory=ComponentAccessibility)
    interactions: InteractionDescriptor = field(default_factory=InteractionDescriptor)
    render_hints: ComponentRenderHints = field(default_factory=ComponentRenderHints)
    bindings: list[ComponentDataBinding] = field(default_factory=list)
    children: list[Component] = field(default_factory=list)
    states: dict[str, bool] = field(default_factory=dict)
    events: dict[InteractionType, list[ComponentEventHandler]] = field(default_factory=dict)
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
    shortcuts: list[str] = field(default_factory=list)
    locale: str | None = None
    timestamp: float | None = None
    animations: list[str] = field(default_factory=list)
    transitions: list[str] = field(default_factory=list)
    visible: bool = True
    enabled: bool = True
    focusable: bool = False

    def __post_init__(self) -> None:
        """Finalize component metadata after initialization."""
        resolved_name = self.component_name or self.name or type(self).__name__
        self.component_name = resolved_name

    def set_style_name(self, name: str) -> None:
        """Deprecated shim retaining compatibility with previous API."""
        self.component_name = name

    def set_state(self, state: str, active: bool) -> None:
        """Toggle a named state flag."""
        self.states[state] = active

    def register_event_handler(self, interaction: InteractionType, handler: ComponentEventHandler) -> None:
        """Register ``handler`` for ``interaction`` events."""
        handlers = self.events.setdefault(interaction, [])
        handlers.append(handler)

    def emit(
        self,
        interaction: InteractionType,
        payload: Any | None = None,
        *,
        timestamp: float | None = None,
    ) -> None:
        """Invoke registered handlers for ``interaction``."""
        from ornata.definitions.dataclasses.events import ComponentEvent
        event = ComponentEvent(
            name=interaction.value,
            component_id=self.component_id,
            payload=payload,
            timestamp=timestamp,
            metadata=self.meta or None,
        )
        for handler in self.events.get(interaction, []):
            handler(event)

    def add_child(self, component: Component) -> None:
        """Append ``component`` as a child."""
        self.children.append(component)

    def extend_children(self, nodes: Iterable[Component]) -> None:
        """Append multiple child nodes."""
        self.children.extend(nodes)

    def iter_children(self) -> tuple[Component, ...]:
        """Return an immutable snapshot of child components."""
        return tuple(self.children)

    def hydrate(self, dataset: Mapping[str, Any]) -> None:
        """Merge ``dataset`` into the data dictionary."""
        self.data.update(dataset)

    def render(self) -> str | Iterable[str] | None:
        """Render this component to textual output."""
        return None

    def measure(self) -> ComponentMeasurement:
        """Estimate the dimensions for this component."""
        text_width, text_height = self._estimate_text_metrics()
        return ComponentMeasurement(width=text_width, height=text_height)

    def get_layout_style(self) -> LayoutStyle:
        """Construct a layout style compatible with the layout engine."""
        from ornata.api.exports.components import _load_layout_style_class
        layout_style_cls = _load_layout_style_class()
        style = layout_style_cls()
        style.display = "block" if self.visible else "none"
        if any((self.placement.x, self.placement.y, self.placement.z_index is not None)):
            style.position = "absolute"
        return style

    def describe(self) -> dict[str, Any]:
        """Return a renderer-friendly snapshot of this component."""
        return {
            "component_id": self.component_id,
            "component_name": self.component_name,
            "kind": self.kind.value,
            "variant": self.variant,
            "intent": self.intent,
            "role": self.role,
            "content": self.content,
            "placement": self.placement,
            "states": self.states.copy(),
            "data": self.data.copy(),
            "meta": self.meta.copy(),
            "visible": self.visible,
            "enabled": self.enabled,
            "focusable": self.focusable,
            "children": [child.describe() for child in self.children],
        }

    def _estimate_text_metrics(self) -> tuple[float, float]:
        """Estimate width/height metrics from textual content."""
        from ornata.definitions.constants import DEFAULT_COMPONENT_HEIGHT, DEFAULT_COMPONENT_WIDTH
        lines: list[str] = []
        candidates = [
            self.content.text,
            self.content.body,
            self.content.title,
            self.content.subtitle,
            self.content.caption,
        ]
        for candidate in candidates:
            if isinstance(candidate, str) and candidate:
                lines.extend(candidate.splitlines() or [candidate])
        for paragraph in self.content.paragraphs:
            if paragraph:
                lines.extend(paragraph.splitlines() or [paragraph])
        if not lines:
            return DEFAULT_COMPONENT_WIDTH, DEFAULT_COMPONENT_HEIGHT
        width = max(len(line) for line in lines) or DEFAULT_COMPONENT_WIDTH
        height = max(len(lines), 1)
        return float(width), float(height)

__all__ = [
    "Component",
    "ComponentAccessibility",
    "ComponentContent",
    "ComponentDataBinding",
    "ComponentInfo",
    "ComponentMeasurement",
    "ComponentPlacement",
    "ComponentRenderHints",
    "ComponentRule",
    "ComponentVersion",
    "InteractionDescriptor",
    "StateBlock",
    "VersionConstraint",
]
