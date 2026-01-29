"""VDOM-Renderer Bridge System for complete integration.

This module provides the main bridge between VDOM processing and rendering backends,
ensuring proper VDOM tree to rendering integration layer. It connects VDOM processing
to actual renderer consumption while following AGENTS.md import patterns.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import BackendTarget, Patch, StandardHostObject, VDOMRendererContext, VDOMTree
    from ornata.rendering.core.base_renderer import Renderer

logger = get_logger(__name__)


class VDOMRendererBridge:
    """Main bridge system connecting VDOM processing to rendering backends.
    
    This class provides the central integration point for VDOM tree processing
    and rendering, ensuring proper patch application and host object lifecycle.
    """
    
    def __init__(self) -> None:
        """Initialize the VDOM-Renderer Bridge."""
        self._contexts: dict[BackendTarget, VDOMRendererContext] = {}
        self._context_lock = threading.RLock()
        logger.debug("VDOM-Renderer Bridge initialized")
    
    def register_renderer(
        self, 
        backend_target: BackendTarget, 
        renderer_instance: Renderer
    ) -> VDOMRendererContext:
        """Register a renderer with the VDOM-Renderer Bridge.
        
        Parameters
        ----------
        backend_target : BackendTarget
            The backend target to register.
        renderer_instance : Renderer
            The renderer instance to register.
            
        Returns
        -------
        VDOMRendererContext
            The created or existing context for this renderer.
            
        Raises
        ------
        ValueError
            If the renderer type is not supported.
        """
        from ornata.api.exports.definitions import VDOMRendererContext
        from ornata.rendering.adapters.base import AdapterFactory
        
        with self._context_lock:
            # Check if we already have a context for this renderer
            if backend_target in self._contexts:
                context = self._contexts[backend_target]
                if context.backend_instance is renderer_instance:
                    logger.debug(f"Reusing existing context for {backend_target}")
                    return context
                else:
                    # Different instance, need to update
                    context.cleanup()
            
            # Create new adapter
            try:
                adapter = AdapterFactory.create_adapter(backend_target, renderer_instance)
                adapter.initialize()
            except ValueError as e:
                logger.error(f"No adapter available for renderer type {backend_target}: {e}")
                raise ValueError(f"Unsupported renderer type: {backend_target}") from e
            
            # Create new context
            context = VDOMRendererContext(
                backend_target=backend_target,
                backend_instance=renderer_instance,
                adapter=adapter
            )
            
            self._contexts[backend_target] = context
            logger.debug(f"Registered renderer {backend_target} with VDOM-Renderer Bridge")
            return context
    
    def render_vdom_tree(
        self, 
        vdom_tree: VDOMTree, 
        backend_target: BackendTarget | None = None
    ) -> Any:
        """Render a VDOM tree using the specified or tree's renderer type.
        
        Parameters
        ----------
        vdom_tree : VDOMTree
            The VDOM tree to render.
        backend_target : BackendTarget | None
            The backend target to use. If None, uses vdom_tree.backend_target.
            
        Returns
        -------
        Any
            Renderer-specific output.
            
        Raises
        ------
        ValueError
            If the backend is not registered.
        """
        if backend_target is None:
            backend_target = vdom_tree.backend_target
        
        # Get or create context
        try:
            context = self._contexts[backend_target]
        except KeyError as e:
            raise ValueError(f"Backend {backend_target} is not registered with the bridge") from e
        
        # Ensure initialization
        context.ensure_initialized()
        
        # Convert VDOM tree using adapter
        try:
            # 1. Convert VDOM to renderer-specific structure (e.g. GuiNode tree)
            renderer_tree = context.adapter.convert_tree(vdom_tree)
            
            # 2. Pass the converted tree to the actual renderer
            # The renderer instance (e.g. WindowRenderer) knows how to draw this structure
            output = context.backend_instance.render_tree(renderer_tree, None)
            
            logger.debug(f"Rendered VDOM tree for {backend_target}")
            return output
        except Exception as e:
            logger.error(f"Failed to render VDOM tree for {backend_target}: {e}")
            raise
    
    def apply_vdom_patches(
        self, 
        patches: list[Patch], 
        backend_target: BackendTarget
    ) -> None:
        """Apply VDOM patches to a specific renderer.
        
        Parameters
        ----------
        patches : list[Patch]
            VDOM patches to apply.
        backend_target : BackendTarget
            The backend target to apply patches to.
            
        Raises
        ------
        ValueError
            If the backend is not registered.
        """
        try:
            context = self._contexts[backend_target]
        except KeyError as e:
            raise ValueError(f"Backend {backend_target} is not registered with the bridge") from e
        
        # Ensure initialization
        context.ensure_initialized()
        
        with context.lock:
            try:
                # Apply patches through adapter to update internal state/mappings
                context.adapter.apply_patches(patches)
                
                # Forward patches to the actual renderer for visual updates
                context.backend_instance.apply_patches(patches)
                
                # Update bindings registry for host objects
                for patch in patches:
                    if patch.key is not None:
                        if patch.patch_type.name == "ADD_NODE":
                            # Register new host object in bindings
                            host_obj = context.adapter.context.get_host_object(patch.key)
                            if host_obj is not None:
                                from ornata.vdom.core.binding_integration import bind_host_object_to_tree
                                bind_host_object_to_tree(
                                    backend_target, patch.key, host_obj, context.bindings_registry
                                )
                        elif patch.patch_type.name == "REMOVE_NODE":
                            # Unregister from bindings
                            context.bindings_registry.remove_by_key(backend_target, patch.key)
                
                logger.debug(f"Applied {len(patches)} patches to {backend_target}")
            except Exception as e:
                logger.error(f"Failed to apply patches to {backend_target}: {e}")
                raise
    
    def get_host_object(
        self, 
        backend_target: BackendTarget, 
        vdom_key: str
    ) -> StandardHostObject | None:
        """Get a host object for a VDOM key from a specific renderer."""
        try:
            context = self._contexts[backend_target]
        except KeyError:
            return None
        
        return context.bindings_registry.lookup_by_key(backend_target, vdom_key)
    
    def get_renderer_object(
        self, 
        backend_target: BackendTarget, 
        vdom_key: str
    ) -> Any:
        """Get a renderer object for a VDOM key from a specific renderer."""
        try:
            context = self._contexts[backend_target]
        except KeyError:
            return None
        
        return context.adapter.context.get_backend_object(vdom_key)
    
    def unregister_renderer(self, backend_target: BackendTarget) -> None:
        """Unregister a renderer from the VDOM-Renderer Bridge."""
        with self._context_lock:
            context = self._contexts.pop(backend_target, None)
            if context is not None:
                context.cleanup()
                logger.debug(f"Unregistered renderer {backend_target} from VDOM-Renderer Bridge")
    
    def get_registered_renderers(self) -> list[BackendTarget]:
        """Get list of registered renderer types."""
        with self._context_lock:
            return list(self._contexts.keys())
    
    def cleanup_all(self) -> None:
        """Cleanup all registered renderers and contexts."""
        with self._context_lock:
            for context in self._contexts.values():
                try:
                    context.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up context for {context.backend_target}: {e}")
            
            self._contexts.clear()
            logger.debug("Cleaned up all VDOM-renderer contexts")


# Global bridge instance
_global_bridge = VDOMRendererBridge()
_bridge_lock = threading.RLock()


def get_vdom_renderer_bridge() -> VDOMRendererBridge:
    """Get the global VDOM-Renderer Bridge instance."""
    with _bridge_lock:
        return _global_bridge