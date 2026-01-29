"""Base VDOM adapter interface for all renderer types.

This module defines the common interface that all VDOM renderer adapters must implement
to bridge VDOM tree structures to renderer-specific primitives.
"""

from __future__ import annotations

import threading
from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import (
    AdapterContext,
    DefaultHostObject,
    StandardHostObject,
)
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import BackendTarget, Patch, StandardHostObject, VDOMTree
    from ornata.vdom.core.tree import VDOMNode

logger = get_logger(__name__)


class VDOMAdapter:
    """Base interface for VDOM-to-renderer adapters.
    
    Adapters translate VDOM tree structures into renderer-specific primitives
    while maintaining the benefits of VDOM diffing and patch application.
    """
    
    def __init__(self, backend_target: BackendTarget, renderer_instance: Any) -> None:
        """Initialize the VDOM adapter.
        
        Parameters
        ----------
        backend_target : BackendTarget
            The type of renderer this adapter serves.
        renderer_instance : Any
            The concrete renderer instance.
        """
        self.backend_target = backend_target
        self.renderer_instance = renderer_instance
        self.context = AdapterContext(backend_target, renderer_instance)
        self._initialized = False
        
        logger.debug(f"Initialized VDOM adapter for {backend_target}")
    
    def initialize(self) -> None:
        """Initialize the adapter with renderer-specific setup."""
        if self._initialized:
            return
        
        with self.context._lock:
            try:
                self._do_initialize()
                self._initialized = True
                logger.debug(f"VDOM adapter initialized for {self.backend_target}")
            except Exception as e:
                logger.error(f"Failed to initialize VDOM adapter: {e}")
                raise
    
    @abstractmethod
    def _do_initialize(self) -> None:
        """Renderer-specific initialization logic.
        
        Subclasses must implement this method to perform renderer-specific setup.
        """
        ...
    
    @abstractmethod
    def convert_tree(self, vdom_tree: VDOMTree) -> Any:
        """Convert a VDOM tree to renderer-specific format.
        
        Parameters
        ----------
        vdom_tree : VDOMTree
            The VDOM tree to convert.
            
        Returns
        -------
        Any
            Renderer-specific tree representation.
        """
        ...
    
    @abstractmethod
    def convert_node(self, node: VDOMNode) -> Any:
        """Convert a VDOM node to renderer-specific format.
        
        Parameters
        ----------
        node : VDOMNode
            The VDOM node to convert.
            
        Returns
        -------
        Any
            Renderer-specific node representation.
        """
        ...
    
    @abstractmethod
    def apply_patches(self, patches: list[Patch]) -> None:
        """Apply VDOM patches to the renderer.
        
        Parameters
        ----------
        patches : list[Patch]
            VDOM patches to apply.
        """
        ...
    
    def create_host_object(self, node: VDOMNode) -> DefaultHostObject | StandardHostObject:
        """Create a host object for a VDOM node.
        
        Default implementation creates a basic host wrapper.
        
        Parameters
        ----------
        node : VDOMNode
            The VDOM node to create host for.
            
        Returns
        -------
        DefaultHostObject | StandardHostObject
            The created host object.
        """
        # Default implementation - subclasses can override for custom host objects
        return DefaultHostObject(
            vdom_key=node.key or "unknown",
            component_name=node.component_name,
            props=node.props,
            children_count=len(node.children)
        )
    
    def apply_props_to_host(self, host: StandardHostObject, props: dict[str, Any]) -> None:
        """Apply properties to a host object.
        
        Default implementation updates props in DefaultHostObject.
        
        Parameters
        ----------
        host : StandardHostObject
            The host object to update.
        props : dict[str, Any]
            Properties to apply.
        """
        if isinstance(host, DefaultHostObject):
            host.props.update(props)
            logger.debug(f"Applied props to host {host.component_name}: {list(props.keys())}")
    
    def cleanup(self) -> None:
        """Cleanup adapter resources."""
        with self.context._lock:
            self.context.node_mapping.clear()
            self.context.host_objects.clear()
            logger.debug(f"Cleaned up VDOM adapter for {self.backend_target}")


class AdapterFactory:
    """Factory for creating VDOM adapters."""
    
    _adapters: dict[BackendTarget, type[VDOMAdapter]] = {}
    _instances: dict[tuple[BackendTarget, Any], VDOMAdapter] = {}
    _lock = threading.RLock()
    
    @classmethod
    def register_adapter(cls, backend_target: BackendTarget, adapter_class: type[VDOMAdapter]) -> None:
        """Register an adapter class for a renderer type.
        
        Parameters
        ----------
        backend_target : BackendTarget
            The renderer type to register for.
        adapter_class : type[VDOMAdapter]
            The adapter class to register.
        """
        with cls._lock:
            cls._adapters[backend_target] = adapter_class
            logger.debug(f"Registered adapter {adapter_class.__name__} for {backend_target}")
    
    @classmethod
    def create_adapter(cls, backend_target: BackendTarget, renderer_instance: Any) -> VDOMAdapter:
        """Create an adapter instance for a renderer.
        
        Parameters
        ----------
        renderer_type : RendererType
            The type of renderer.
        renderer_instance : Any
            The renderer instance.
            
        Returns
        -------
        VDOMAdapter
            The created adapter instance.
        """
        with cls._lock:
            # Check if we already have an instance
            key = (backend_target, id(renderer_instance))
            if key in cls._instances:
                return cls._instances[key]
            
            # Get adapter class
            adapter_class = cls._adapters.get(backend_target)
            if adapter_class is None:
                raise ValueError(f"No adapter registered for renderer type {backend_target}")
            
            # Create instance
            adapter = adapter_class(backend_target, renderer_instance)
            cls._instances[key] = adapter
            return adapter
    
    @classmethod
    def get_registered_types(cls) -> list[BackendTarget]:
        """Get list of registered renderer types.
        
        Returns
        -------
        list[RendererType]
            List of registered renderer types.
        """
        with cls._lock:
            return list(cls._adapters.keys())
