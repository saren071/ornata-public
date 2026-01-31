""" Core Dataclasses for Ornata """

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ornata.definitions.dataclasses.layout import Bounds
from ornata.definitions.enums import AssetType, BackendTarget

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ornata.definitions.dataclasses.components import Component
    from ornata.definitions.dataclasses.layout import LayoutResult
    from ornata.definitions.dataclasses.rendering import GuiNode
    from ornata.definitions.dataclasses.styling import ResolvedStyle


@dataclass(slots=True)
class AppConfig:
    """Configuration settings for an Ornata application."""
    title: str = "Ornata Application"
    backend: BackendTarget = BackendTarget.CLI
    viewport_width: int = 120
    viewport_height: int = 40
    stylesheets: list[str] = field(default_factory=list)
    capabilities: dict[str, object] = field(default_factory=dict)

    def backend_target(self) -> BackendTarget:
        return self.backend

    def viewport_bounds(self) -> Bounds:
        """Return viewport bounds appropriate for the backend.
        
        For CLI/TTY backends, dimensions are already in cell units (columns/rows)
        as detected from the terminal. For GUI backends, returns pixel-based bounds.
        """
        # For CLI backends, dimensions are already in cells (from terminal detection)
        if self.backend in (BackendTarget.CLI, BackendTarget.TTY):
            # Use detected terminal size directly, with fallback to defaults if zero
            cell_width = self.viewport_width if self.viewport_width > 0 else 80
            cell_height = self.viewport_height if self.viewport_height > 0 else 24
            return Bounds(x=0, y=0, width=cell_width, height=cell_height)
        return Bounds(x=0, y=0, width=self.viewport_width, height=self.viewport_height)

    def combined_capabilities(self) -> dict[str, object]:
        merged = dict(self.backend.default_capabilities())
        merged.update(self.capabilities)
        return merged


@dataclass(slots=True)
class RuntimeFrame:
    """Result of a single orchestration pass through styling, VDOM, and layout."""
    root: Component
    layout: LayoutResult
    styles: Mapping[int, ResolvedStyle]
    gui_tree: GuiNode


@dataclass(slots=True, weakref_slot=True)
class BaseHostObject:
    """Base implementation of StandardHostObject protocol with common functionality."""

    vdom_key: str
    component_name: str
    backend_target: BackendTarget
    _active: bool = field(default=True, init=False)
    _properties: dict[str, Any] = field(default_factory=dict, init=False)
    _event_handlers: dict[str, list[Any]] = field(default_factory=dict, init=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False)

    def __post_init__(self) -> None:
        """Initialize the base host object after dataclass creation."""
        # Initialize with empty properties if not provided
        if not hasattr(self, "_properties"):
            self._properties = {}
        if not hasattr(self, "_event_handlers"):
            self._event_handlers = {}


@dataclass(slots=True, frozen=True)
class AssetInfo:
    """Metadata describing a registered asset."""
    asset_id: str
    asset_type: AssetType
    source: str | None = None
    size_bytes: int | None = None
    checksum: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

__all__ = [
    "AppConfig",
    "RuntimeFrame",
    "BaseHostObject",
    "AssetInfo",
]
