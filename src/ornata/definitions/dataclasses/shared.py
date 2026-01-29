""" Shared Dataclasses for Ornata """

from __future__ import annotations

import copy
import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ornata.api.exports.vdom import HostBindingRegistry, get_bindings_registry
from ornata.definitions.dataclasses.core import BaseHostObject

if TYPE_CHECKING:
    from ornata.api.exports.rendering import Renderer, VDOMAdapter
    from ornata.definitions.enums import BackendTarget

@dataclass(slots=True)
class VDOMRendererContext:
    """Context for VDOM-renderer integration."""
    backend_target: BackendTarget
    backend_instance: Renderer
    adapter: VDOMAdapter
    bindings_registry: HostBindingRegistry = field(default_factory=get_bindings_registry)
    _lock: threading.RLock = field(default_factory=threading.RLock)
    is_initialized: bool = False
    
    def ensure_initialized(self) -> None:
        with self._lock:
            if not self.is_initialized:
                try:
                    self.adapter.initialize()
                    self.is_initialized = True
                except Exception:
                    raise
    
    def cleanup(self) -> None:
        with self._lock:
            if self.is_initialized:
                try:
                    self.adapter.cleanup()
                    self.bindings_registry.cleanup_dead()
                    self.is_initialized = False
                except Exception:
                    pass

    @property
    def lock(self) -> threading.RLock:
        return self._lock


@dataclass(slots=True)
class AdapterContext:
    """Context for VDOM adapter operations."""
    backend_target: BackendTarget
    backend_instance: Any
    _lock: threading.RLock = field(default_factory=threading.RLock)
    node_mapping: dict[str, Any] = field(default_factory=dict)
    host_objects: dict[str, StandardHostObject] = field(default_factory=dict)
    
    def register_node_mapping(self, vdom_key: str, backend_object: Any) -> None:
        with self._lock:
            self.node_mapping[vdom_key] = backend_object
    
    def get_backend_object(self, vdom_key: str) -> Any | None:
        with self._lock:
            return self.node_mapping.get(vdom_key)
    
    def register_host_object(self, vdom_key: str, host: StandardHostObject) -> None:
        with self._lock:
            self.host_objects[vdom_key] = host
 
    def get_host_object(self, vdom_key: str) -> StandardHostObject | None:
        with self._lock:
            return self.host_objects.get(vdom_key)


@dataclass(slots=True, frozen=True)
class DefaultHostObject:
    """Default host object implementation for basic VDOM integration."""
    vdom_key: str
    component_name: str
    props: dict[str, Any] = field(default_factory=dict)
    children_count: int = 0


@dataclass(slots=True)
class StandardHostObject(BaseHostObject):
    """Standard host object implementation that fully implements the HostObjectProtocol."""

    def __post_init__(self) -> None:
        super().__post_init__()

    def initialize(self, vdom_node: Any) -> None:
        with self._lock:
            if hasattr(vdom_node, "props") and vdom_node.props:
                self._properties.update(vdom_node.props)
            if not self.component_name and hasattr(vdom_node, "component_name"):
                self.component_name = vdom_node.component_name

    def update_properties(self, properties: dict[str, Any]) -> None:
        with self._lock:
            self._properties.update(properties)

    def destroy(self) -> None:
        with self._lock:
            self._properties.clear()
            self._event_handlers.clear()
            self._active = False

    @property
    def is_active(self) -> bool:
        with self._lock:
            return self._active

    def set_active(self, active: bool) -> None:
        with self._lock:
            self._active = active

    @property
    def properties(self) -> dict[str, Any]:
        with self._lock:
            return self._properties.copy()

    def get_property(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._properties.get(key, default)

    def set_property(self, key: str, value: Any) -> None:
        with self._lock:
            self._properties[key] = value

    def handle_event(self, event_type: str, event_data: dict[str, Any]) -> bool:
        with self._lock:
            handlers = self._event_handlers.get(event_type, [])
            if not handlers:
                return False
            handled = False
            for handler in handlers:
                try:
                    result = handler(event_type, event_data, self)
                    if result is not False:
                        handled = True
                except Exception:
                    pass
            return handled

    def add_event_handler(self, event_type: str, handler: Any) -> None:
        with self._lock:
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(handler)

    def remove_event_handler(self, event_type: str, handler: Any) -> None:
        with self._lock:
            if event_type in self._event_handlers:
                try:
                    self._event_handlers[event_type].remove(handler)
                except ValueError:
                    pass

    def get_debug_info(self) -> dict[str, Any]:
        with self._lock:
            return {
                "vdom_key": self.vdom_key,
                "component_name": self.component_name,
                "backend_target": str(self.backend_target),
                "is_active": self._active,
                "properties_count": len(self._properties),
                "event_handlers_count": sum(len(handlers) for handlers in self._event_handlers.values()),
                "properties": self._properties.copy(),
                "event_types": list(self._event_handlers.keys()),
            }

    def clone(self) -> StandardHostObject:
        with self._lock:
            cloned = StandardHostObject(
                vdom_key=self.vdom_key,
                component_name=self.component_name,
                backend_target=self.backend_target,
            )
            try:
                cloned._properties.update(copy.deepcopy(self._properties))
            except Exception:
                cloned._properties.update(self._properties.copy())
            cloned._event_handlers = {k: list(v) for k, v in self._event_handlers.items()}
            cloned._active = self._active
            return cloned

__all__ = [
    "AdapterContext",
    "DefaultHostObject",
    "StandardHostObject",
    "VDOMRendererContext",
]