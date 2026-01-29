"""Type stubs for the layout subsystem exports."""

from __future__ import annotations

from ornata.layout import adapters as adapters
from ornata.layout import algorithms as algorithms
from ornata.layout import diagnostics as diagnostics
from ornata.layout import engine as engine
from ornata.layout import geometry as geometry
from ornata.layout import scrolling as scrolling
from ornata.layout.adapters import osts_converter as osts_converter
from ornata.layout.adapters.osts_converter import OSTSLayoutConverter as OSTSLayoutConverter
from ornata.layout.adapters.osts_converter import get_osts_converter as get_osts_converter
from ornata.layout.adapters.osts_converter import osts_to_layout_style as osts_to_layout_style
from ornata.layout.algorithms import absolute as absolute
from ornata.layout.algorithms import flex as flex
from ornata.layout.algorithms import grid as grid
from ornata.layout.algorithms import responsive as responsive
from ornata.layout.algorithms.responsive import ResponsiveLayoutManager as ResponsiveLayoutManager
from ornata.layout.algorithms.responsive import adapt_layout_responsive as adapt_layout_responsive
from ornata.layout.algorithms.responsive import get_responsive_manager as get_responsive_manager
from ornata.layout.core import constraints as constraints
from ornata.layout.core.constraints import AspectRatioConstraint as AspectRatioConstraint
from ornata.layout.core.constraints import BaseLayoutConstraint as BaseLayoutConstraint
from ornata.layout.core.constraints import ConstraintSolver as ConstraintSolver
from ornata.layout.core.constraints import ContainerFitConstraint as ContainerFitConstraint
from ornata.layout.core.constraints import MaxSizeConstraint as MaxSizeConstraint
from ornata.layout.core.constraints import MinSizeConstraint as MinSizeConstraint
from ornata.layout.core.constraints import SpatialIndex as SpatialIndex
from ornata.layout.core.constraints import SpatialIndexEntry as SpatialIndexEntry
from ornata.layout.core.utils import align_text as align_text
from ornata.layout.core.utils import clamp_int as clamp_int
from ornata.layout.core.utils import compute_justify_spacing as compute_justify_spacing
from ornata.layout.diagnostics import debug as debug
from ornata.layout.diagnostics.debug import LayoutDebugger as LayoutDebugger
from ornata.layout.diagnostics.debug import LayoutDebugInfo as LayoutDebugInfo
from ornata.layout.diagnostics.debug import get_layout_debugger as get_layout_debugger
from ornata.layout.engine.engine import LayoutEngine as LayoutEngine
from ornata.layout.engine.engine import LayoutNode as LayoutNode
from ornata.layout.engine.engine import LayoutResult as LayoutResult
from ornata.layout.engine.engine import LayoutStyle as LayoutStyle
from ornata.layout.engine.engine import _calculate_grid_track_sizes as _calculate_grid_track_sizes  #type: ignore
from ornata.layout.engine.engine import _parse_grid_template as _parse_grid_template  #type: ignore
from ornata.layout.engine.engine import calculate_component_layout as calculate_component_layout
from ornata.layout.engine.engine import component_to_layout_node as component_to_layout_node
from ornata.layout.engine.engine import compute_absolute_layout as compute_absolute_layout
from ornata.layout.engine.engine import compute_grid as compute_grid
from ornata.layout.engine.engine import compute_grid_layout as compute_grid_layout
from ornata.layout.engine.engine import compute_layout as compute_layout
from ornata.layout.engine.engine import compute_relative_layout as compute_relative_layout
from ornata.layout.engine.engine import measure_leaf as measure_leaf
from ornata.layout.geometry.dirty_rectangles import DirtyRectangleContext as DirtyRectangleContext
from ornata.layout.geometry.dirty_rectangles import DirtyRectangleRenderer as DirtyRectangleRenderer
from ornata.layout.geometry.dirty_rectangles import RenderBatch as RenderBatch
from ornata.layout.geometry.dirty_rectangles import RenderCallback as RenderCallback
from ornata.layout.geometry.dirty_rectangles import dirty_rectangles as dirty_rectangles
from ornata.layout.geometry.dirty_rectangles import get_dirty_renderer as get_dirty_renderer
from ornata.layout.scrolling import virtual_scrolling as virtual_scrolling
from ornata.layout.scrolling.virtual_scrolling import VirtualScrollConfig as VirtualScrollConfig
from ornata.layout.scrolling.virtual_scrolling import VirtualScrollContainer as VirtualScrollContainer
from ornata.layout.scrolling.virtual_scrolling import VirtualScrollState as VirtualScrollState
from ornata.layout.scrolling.virtual_scrolling import create_simple_item_renderer as create_simple_item_renderer
from ornata.layout.scrolling.virtual_scrolling import create_virtual_scroll_node as create_virtual_scroll_node

__all__ = [
    "AspectRatioConstraint",
    "BaseLayoutConstraint",
    "ConstraintSolver",
    "ContainerFitConstraint",
    "DirtyRectangleContext",
    "DirtyRectangleRenderer",
    "LayoutDebugInfo",
    "LayoutDebugger",
    "LayoutEngine",
    "LayoutNode",
    "LayoutResult",
    "LayoutStyle",
    "MaxSizeConstraint",
    "MinSizeConstraint",
    "RenderBatch",
    "RenderCallback",
    "ResponsiveLayoutManager",
    "SpatialIndex",
    "SpatialIndexEntry",
    "OSTSLayoutConverter",
    "VirtualScrollConfig",
    "VirtualScrollContainer",
    "VirtualScrollState",
    "_calculate_grid_track_sizes",
    "_parse_grid_template",
    "absolute",
    "adapt_layout_responsive",
    "adapters",
    "algorithms",
    "align_text",
    "calculate_component_layout",
    "clamp_int",
    "component_to_layout_node",
    "compute_absolute_layout",
    "compute_grid",
    "compute_grid_layout",
    "compute_justify_spacing",
    "compute_layout",
    "compute_relative_layout",
    "constraints",
    "create_simple_item_renderer",
    "create_virtual_scroll_node",
    "debug",
    "diagnostics",
    "dirty_rectangles",
    "engine",
    "flex",
    "geometry",
    "get_dirty_renderer",
    "get_layout_debugger",
    "get_responsive_manager",
    "get_osts_converter",
    "grid",
    "measure_leaf",
    "responsive",
    "scrolling",
    "osts_converter",
    "osts_to_layout_style",
    "virtual_scrolling",
]