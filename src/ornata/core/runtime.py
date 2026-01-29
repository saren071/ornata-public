"""Runtime orchestration for public Ornata applications."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.definitions.dataclasses.core import AppConfig, RuntimeFrame
from ornata.definitions.dataclasses.rendering import GuiNode
from ornata.definitions.dataclasses.styling import Insets, ResolvedStyle, StylingContext
from ornata.definitions.dataclasses.vdom import VDOMTree
from ornata.layout.engine.engine import LayoutEngine, LayoutNode, compute_layout
from ornata.styling.runtime import StylingRuntime
from ornata.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from ornata.definitions.dataclasses.components import Component
    from ornata.definitions.dataclasses.layout import LayoutStyle
    from ornata.definitions.dataclasses.styling import ResolvedStyle


class OrnataRuntime:
    """Coordinates styling, VDOM, layout, and renderer selection."""

    def __init__(self, config: AppConfig) -> None:
        """Create a runtime bound to ``config``."""

        self._config = config
        self._backend_target = config.backend_target()
        self._logger = get_logger(__name__)
        self._styling = StylingRuntime()
        self._layout_engine = LayoutEngine()
        self._stylesheets_loaded: set[str] = set()
        self._vdom_tree = VDOMTree(backend_target=self._backend_target)
        self._layout_tree: LayoutNode | None = None
        self._last_gui_tree: GuiNode | None = None
        for stylesheet in config.stylesheets:
            self.load_stylesheet(stylesheet)

    def load_stylesheet(self, path: str) -> None:
        """Load an OST stylesheet once for this runtime."""

        if path in self._stylesheets_loaded:
            return
        self._styling.load_stylesheet(path)
        self._stylesheets_loaded.add(path)
        self._logger.debug("Loaded stylesheet %s", path)

    def run(self, root_component: Component) -> RuntimeFrame:
        """Execute one orchestration pass for ``root_component``."""

        self._logger.info("Mounting root component %s", root_component.component_name)
        self._vdom_tree = VDOMTree(backend_target=self._backend_target)
        key = self._vdom_tree.add_component(root_component)
        self._vdom_tree.root = self._vdom_tree.key_map.get(key)

        styles = self._resolve_styles(root_component)
        layout_tree, binding_map = self._build_layout_tree(root_component, styles)
        self._layout_tree = layout_tree

        bounds = self._config.viewport_bounds()
        layout_result = self._layout_engine.calculate_layout(root_component, bounds, self._backend_target)
        try:
            compute_layout(layout_tree, int(bounds.width), int(bounds.height))
        except Exception as exc:
            self._logger.debug("Legacy layout propagation failed: %s", exc)
        gui_tree = self._build_gui_tree(root_component, binding_map, styles)
        self._last_gui_tree = gui_tree
        self._logger.info("Layout calculated width=%s height=%s", layout_result.width, layout_result.height)
        return RuntimeFrame(root=root_component, layout=layout_result, styles=styles, gui_tree=gui_tree)

    @property
    def vdom_tree(self) -> VDOMTree:
        """Return the most recently produced VDOM tree."""

        return self._vdom_tree

    @property
    def last_gui_tree(self) -> GuiNode | None:
        """Return the most recently built GUI tree, if available."""

        return self._last_gui_tree

    def _build_layout_tree(self, root: Component, styles: dict[int, ResolvedStyle]) -> tuple[LayoutNode, dict[int, LayoutNode]]:
        """Convert the component tree into a LayoutNode hierarchy."""

        bindings: dict[int, LayoutNode] = {}

        def _convert(component: Component) -> LayoutNode:
            measure = self._make_measure_callback(component)
            node = LayoutNode(style=component.get_layout_style(), measure=measure)

            if id(component) in styles:
                self._apply_resolved_style(node.style, styles[id(component)])

            bindings[id(component)] = node
            for child in component.iter_children():
                node.add(_convert(child))
            return node

        return _convert(root), bindings

    def _apply_resolved_style(self, layout_style: LayoutStyle, resolved: ResolvedStyle) -> None:
        """Apply resolved OSTS properties to the layout style.

        Args:
            layout_style (LayoutStyle): The target layout style to mutate.
            resolved (ResolvedStyle): The source resolved style.

        Returns:
            None
        """
        # DEBUG PRINT
        self._logger.debug(f"Applying style to node. Width={resolved.width}, Height={resolved.height}")

        if resolved.width is not None:
            layout_style.width = int(resolved.width.value)
        if resolved.height is not None:
            layout_style.height = int(resolved.height.value)
        if resolved.min_width is not None:
            layout_style.min_width = int(resolved.min_width.value)
        if resolved.min_height is not None:
            layout_style.min_height = int(resolved.min_height.value)
        if resolved.max_width is not None:
            layout_style.max_width = int(resolved.max_width.value)
        if resolved.max_height is not None:
            layout_style.max_height = int(resolved.max_height.value)

        if resolved.display:
            layout_style.display = resolved.display
        if resolved.position:
            layout_style.position = resolved.position

        if resolved.flex_direction:
            layout_style.direction = resolved.flex_direction

        if resolved.flex_wrap == "wrap":
            layout_style.wrap = True
        elif resolved.flex_wrap == "nowrap":
            layout_style.wrap = False

        if resolved.justify_content:
            layout_style.justify = resolved.justify_content
        if resolved.align_items:
            layout_style.align = resolved.align_items

        if resolved.flex_grow is not None:
            layout_style.flex_grow = resolved.flex_grow
        if resolved.flex_shrink is not None:
            layout_style.flex_shrink = resolved.flex_shrink
        if resolved.flex_basis is not None:
            layout_style.flex_basis = int(resolved.flex_basis.value)

        if resolved.margin:
            # Simplified margin handling, assuming uniform or specific could be mapped further
            # LayoutStyle supports granular margins, resolved.margin is Insets
            pass  # Use resolved specific margins below

        # Map standard margins if granular ones aren't set (TODO: full expansion)

    def _make_measure_callback(self, component: Component) -> Callable[[int | None, int | None], tuple[int, int]]:
        """Create a measurement callback compatible with the layout engine."""

        def _measure(_: int | None, __: int | None) -> tuple[int, int]:
            measurement = component.measure()
            width = int(getattr(measurement, "width", 0) or 0)
            height = int(getattr(measurement, "height", 0) or 0)
            return max(width, 0), max(height, 0)

        return _measure

    def _resolve_styles(self, root: Component) -> dict[int, ResolvedStyle]:
        """Resolve styles for the component tree rooted at ``root``."""

        components = list(self._iter_components(root))
        if not components:
            return {}

        self._logger.debug(f"Found {len(components)} components")

        caps = self._config.combined_capabilities()
        contexts = [
            StylingContext(
                component_name=component.component_name or type(component).__name__,
                state=component.states,
                theme_overrides=None,
                caps=caps,
            )
            for component in components
        ]

        self._logger.debug(f"Resolving styles for contexts: {[c.component_name for c in contexts]}")
        resolved = self._styling.resolve_styles_parallel(contexts)
        self._logger.debug(f"Resolved {len(resolved)} styles")

        style_map: dict[int, ResolvedStyle] = {}
        for component, style in zip(components, resolved, strict=False):
            style_map[id(component)] = style
        return style_map

    def _build_gui_tree(
        self,
        component: Component,
        bindings: dict[int, LayoutNode],
        styles: dict[int, ResolvedStyle],
    ) -> GuiNode:
        """Construct a GuiNode tree enriched with layout and styling information."""

        layout_node = bindings.get(id(component))
        layout_box = layout_node.layout if layout_node is not None else None
        resolved_style = styles.get(id(component))
        gui_node = GuiNode(
            component_name=component.component_name or type(component).__name__,
            component_id=component.component_id,
            variant=component.variant,
            intent=component.intent,
            role=component.role,
            content=component.content,
            placement=component.placement,
            accessibility=component.accessibility,
            interactions=component.interactions,
            render_hints=component.render_hints,
            bindings=list(component.bindings),
            states=dict(component.states),
            visible=component.visible,
            enabled=component.enabled,
            focusable=component.focusable,
            data=dict(component.data),
            meta=dict(component.meta),
            dataset=list(component.dataset),
            items=list(component.items),
            columns=list(component.columns),
            rows=[list(row) for row in component.rows],
            selection=list(component.selection),
            selection_mode=component.selection_mode,
            sorting=component.sorting,
            grouping=component.grouping,
            filter_expression=component.filter_expression,
            page_index=component.page_index,
            page_size=component.page_size,
            total_count=component.total_count,
            value=component.value,
            secondary_value=component.secondary_value,
            min_value=component.min_value,
            max_value=component.max_value,
            step_value=component.step_value,
            placeholder_value=component.placeholder_value,
            status=component.status,
            icon_slot=component.icon_slot,
            badge_text=component.badge_text,
            tooltip=component.tooltip,
            animations=list(component.animations),
            transitions=list(component.transitions),
            text=self._extract_text(component),
            style=resolved_style,
            layout_style=layout_node.style if layout_node else None,
        )
        self._populate_style_metadata(gui_node, resolved_style)
        if layout_box is not None:
            gui_node.x = int(getattr(layout_box, "x", 0) or 0)
            gui_node.y = int(getattr(layout_box, "y", 0) or 0)
            gui_node.width = int(getattr(layout_box, "width", 0) or 0)
            gui_node.height = int(getattr(layout_box, "height", 0) or 0)

        gui_node.children = [self._build_gui_tree(child, bindings, styles) for child in component.iter_children()]
        return gui_node

    def _extract_text(self, component: Component) -> str | None:
        """Derive a human-readable text snippet from component content."""

        content = component.content
        candidates = [
            content.text,
            content.title,
            content.subtitle,
            content.body,
            content.caption,
        ]
        for candidate in candidates:
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        if content.paragraphs:
            for paragraph in content.paragraphs:
                if paragraph.strip():
                    return paragraph.strip()
        if content.status_text:
            return content.status_text
        if content.placeholder:
            return content.placeholder
        return None

    def _iter_components(self, root: Component) -> Iterable[Component]:
        """Yield ``root`` and all descendants depth-first."""

        yield root
        for child in root.iter_children():
            yield from self._iter_components(child)

    def _populate_style_metadata(self, gui_node: GuiNode, resolved_style: ResolvedStyle | None) -> None:
        if resolved_style is None:
            return

        metadata = gui_node.metadata
        metadata["resolved_style"] = resolved_style
        if resolved_style.color is not None:
            metadata["color"] = resolved_style.color
        if resolved_style.background is not None:
            metadata["background"] = resolved_style.background
        if resolved_style.border is not None:
            metadata["border_width"] = resolved_style.border.width
            metadata["border_style"] = resolved_style.border.style
            metadata["border_color"] = resolved_style.border.color or resolved_style.border_color
            metadata["border"] = resolved_style.border
        elif resolved_style.border_color is not None:
            metadata["border_color"] = resolved_style.border_color
        if resolved_style.border_radius is not None:
            metadata["border_radius"] = (
                resolved_style.border_radius.top_left,
                resolved_style.border_radius.top_right,
                resolved_style.border_radius.bottom_right,
                resolved_style.border_radius.bottom_left,
            )
        if resolved_style.padding is not None:
            metadata["padding"] = self._insets_to_tuple(resolved_style.padding)
        if resolved_style.margin is not None:
            metadata["margin"] = self._insets_to_tuple(resolved_style.margin)
        if resolved_style.font is not None:
            metadata["font"] = resolved_style.font
        if resolved_style.font_size is not None:
            metadata["font_size"] = resolved_style.font_size
        if resolved_style.text_align is not None:
            metadata["text_align"] = resolved_style.text_align
        if resolved_style.text_transform is not None:
            metadata["text_transform"] = resolved_style.text_transform
        if resolved_style.component_extras:
            metadata["component_extras"] = dict(resolved_style.component_extras)

    @staticmethod
    def _insets_to_tuple(insets: Insets | None) -> tuple[float | int | None, float | int | None, float | int | None, float | int | None] | None:
        if insets is None:
            return None
        return (
            getattr(insets, "top", None),
            getattr(insets, "right", None),
            getattr(insets, "bottom", None),
            getattr(insets, "left", None),
        )


__all__ = [
    "OrnataRuntime",
]
