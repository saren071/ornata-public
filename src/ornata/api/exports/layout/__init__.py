"""Auto-generated lazy exports for the layout subsystem."""

from __future__ import annotations

from importlib import import_module

from ornata.api._warnings import setup_internal_warnings

setup_internal_warnings()

_EXPORT_TARGETS: dict[str, str] = {
    "adapters": "ornata.layout:adapters",
    "algorithms": "ornata.layout:algorithms",
    "diagnostics": "ornata.layout:diagnostics",
    "engine": "ornata.layout:engine",
    "geometry": "ornata.layout:geometry",
    "scrolling": "ornata.layout:scrolling",
    "osts_converter": "ornata.layout.adapters:osts_converter",
    "OSTSLayoutConverter": "ornata.layout.adapters.osts_converter:OSTSLayoutConverter",
    "get_osts_converter": "ornata.layout.adapters.osts_converter:get_osts_converter",
    "osts_to_layout_style": "ornata.layout.adapters.osts_converter:osts_to_layout_style",
    "absolute": "ornata.layout.algorithms:absolute",
    "flex": "ornata.layout.algorithms:flex",
    "grid": "ornata.layout.algorithms:grid",
    "responsive": "ornata.layout.algorithms:responsive",
    "ResponsiveLayoutManager": "ornata.layout.algorithms.responsive:ResponsiveLayoutManager",
    "adapt_layout_responsive": "ornata.layout.algorithms.responsive:adapt_layout_responsive",
    "get_responsive_manager": "ornata.layout.algorithms.responsive:get_responsive_manager",
    "constraints": "ornata.layout.core:constraints",
    "AspectRatioConstraint": "ornata.layout.core.constraints:AspectRatioConstraint",
    "BaseLayoutConstraint": "ornata.layout.core.constraints:BaseLayoutConstraint",
    "ConstraintSolver": "ornata.layout.core.constraints:ConstraintSolver",
    "ContainerFitConstraint": "ornata.layout.core.constraints:ContainerFitConstraint",
    "MaxSizeConstraint": "ornata.layout.core.constraints:MaxSizeConstraint",
    "MinSizeConstraint": "ornata.layout.core.constraints:MinSizeConstraint",
    "SpatialIndex": "ornata.layout.core.constraints:SpatialIndex",
    "SpatialIndexEntry": "ornata.layout.core.constraints:SpatialIndexEntry",
    "align_text": "ornata.layout.core.utils:align_text",
    "clamp_int": "ornata.layout.core.utils:clamp_int",
    "compute_justify_spacing": "ornata.layout.core.utils:compute_justify_spacing",
    "debug": "ornata.layout.diagnostics:debug",
    "LayoutDebugger": "ornata.layout.diagnostics.debug:LayoutDebugger",
    "LayoutDebugInfo": "ornata.layout.diagnostics.debug:LayoutDebugInfo",
    "get_layout_debugger": "ornata.layout.diagnostics.debug:get_layout_debugger",
    "AbsoluteLayout": "ornata.layout.algorithms.absolute:AbsoluteLayout",
    "FlexLayout": "ornata.layout.algorithms.flex:FlexLayout",
    "GridLayout": "ornata.layout.algorithms.grid:GridLayout",
    "LayoutEngine": "ornata.layout.engine.engine:LayoutEngine",
    "LayoutNode": "ornata.layout.engine.engine:LayoutNode",
    "LayoutResult": "ornata.layout.engine.engine:LayoutResult",
    "LayoutStyle": "ornata.layout.engine.engine:LayoutStyle",
    "_calculate_grid_track_sizes": "ornata.layout.engine.engine:_calculate_grid_track_sizes",
    "_parse_grid_template": "ornata.layout.engine.engine:_parse_grid_template",
    "calculate_component_layout": "ornata.layout.engine.engine:calculate_component_layout",
    "component_to_layout_node": "ornata.layout.engine.engine:component_to_layout_node",
    "compute_absolute_layout": "ornata.layout.engine.engine:compute_absolute_layout",
    "compute_grid": "ornata.layout.engine.engine:compute_grid",
    "compute_grid_layout": "ornata.layout.engine.engine:compute_grid_layout",
    "compute_layout": "ornata.layout.engine.engine:compute_layout",
    "compute_relative_layout": "ornata.layout.engine.engine:compute_relative_layout",
    "measure_leaf": "ornata.layout.engine.engine:measure_leaf",
    "DirtyRectangleContext": "ornata.layout.geometry.dirty_rectangles:DirtyRectangleContext",
    "DirtyRectangleRenderer": "ornata.layout.geometry.dirty_rectangles:DirtyRectangleRenderer",
    "RenderBatch": "ornata.layout.geometry.dirty_rectangles:RenderBatch",
    "dirty_rectangles": "ornata.layout.geometry.dirty_rectangles:dirty_rectangles",
    "get_dirty_renderer": "ornata.layout.geometry.dirty_rectangles:get_dirty_renderer",
    "virtual_scrolling": "ornata.layout.scrolling:virtual_scrolling",
    "VirtualScrollContainer": "ornata.layout.scrolling.virtual_scrolling:VirtualScrollContainer",
    "VirtualScrollState": "ornata.layout.scrolling.virtual_scrolling:VirtualScrollState",
    "create_simple_item_renderer": "ornata.layout.scrolling.virtual_scrolling:create_simple_item_renderer",
    "create_virtual_scroll_node": "ornata.layout.scrolling.virtual_scrolling:create_virtual_scroll_node"
}

_RESOLVED_EXPORTS: dict[str, object] = {}

__all__ = ["__getattr__"]

def _load_target(name: str) -> object:
    """Load and cache ``name`` for this subsystem.

    Parameters
    ----------
    name : str
        Export name to resolve.

    Returns
    -------
    object
        Resolved attribute from the owning module.

    Raises
    ------
    AttributeError
        If ``name`` is unknown to this subsystem.
    """

    target = _EXPORT_TARGETS.get(name)
    if target is None:
        raise AttributeError(
            "module 'ornata.api.exports.layout' has no attribute {name!r}"
        )
    module_name, _, attr_name = target.partition(':')
    module = import_module(module_name)
    value = getattr(module, attr_name)
    _RESOLVED_EXPORTS[name] = value
    globals()[name] = value
    return value

def __getattr__(name: str) -> object:
    """Resolve an export attribute on first access.

    Parameters
    ----------
    name : str
        Export name requested from this module.

    Returns
    -------
    object
        Resolved export value.

    Raises
    ------
    AttributeError
        If ``name`` is not part of this subsystem.
    """

    if name in _RESOLVED_EXPORTS:
        return _RESOLVED_EXPORTS[name]
    return _load_target(name)

def __dir__() -> list[str]:
    """Return the sorted list of exportable names.

    Returns
    -------
    list[str]
        Sorted names available via this module.
    """

    names = ['__getattr__']
    names.extend(_EXPORT_TARGETS)
    return sorted(names)
