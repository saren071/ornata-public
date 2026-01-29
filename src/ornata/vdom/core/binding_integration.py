"""Integration layer connecting VDOM Bindings Registry to actual renderer objects.

This module provides the bridge between the VDOM binding registry and
rendering systems, enabling seamless VDOM bindings to drive actual
rendering operations across all backends.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger
from ornata.vdom.core.bindings import get_bindings_registry

if TYPE_CHECKING:
    from ornata.api.exports.definitions import BackendTarget, Patch
    from ornata.api.exports.vdom import HostBindingRegistry

logger = get_logger(__name__)


class RendererBindingContext:
    """Context manager for VDOM bindings in a specific backend."""
    
    def __init__(self, backend_target: BackendTarget, renderer_instance: Any) -> None:
        """Initialize the binding context.
        
        Parameters
        ----------
        backend_target : BackendTarget
            The type of renderer this context is for.
        renderer_instance : Any
            The renderer instance.
        """
        self.backend_target = backend_target
        self.renderer_instance = renderer_instance
        self.lock = threading.RLock()
        # Use the global registry to ensure all contexts share the same registry
        self._registry = get_bindings_registry()
        # Host objects are backend-specific; store as Any and rely on hasattr-based shape checks.
        self._active_bindings: dict[str, Any] = {}
        logger.debug(f"Created binding context for {backend_target}")
    
    def register_vdom_binding(self, vdom_key: str, host_obj: Any) -> None:
        """Register a VDOM key to host object binding.
        
        Parameters
        ----------
        vdom_key : str
            The VDOM key to bind.
        host_obj : StandardHostObject
            The host object to bind to.
        """
        with self.lock:
            # Register with the global bindings registry
            self._registry.register_bind(self.backend_target, vdom_key, host_obj)
            
            # Store locally for this context
            self._active_bindings[vdom_key] = host_obj
            
            logger.debug(f"Registered binding: {vdom_key} -> {type(host_obj).__name__}")
    
    def get_host_object(self, vdom_key: str) -> Any | None:
        """Get a host object by VDOM key.
        
        Parameters
        ----------
        vdom_key : str
            The VDOM key to look up.
            
        Returns
        -------
        StandardHostObject | None
            The host object if found, None otherwise.
        """
        with self.lock:
            return self._active_bindings.get(vdom_key)
    
    def unregister_vdom_binding(self, vdom_key: str) -> None:
        """Unregister a VDOM key binding.
        
        Parameters
        ----------
        vdom_key : str
            The VDOM key to unregister.
        """
        with self.lock:
            # Remove from global registry
            self._registry.remove_by_key(self.backend_target, vdom_key)
            
            # Remove from local bindings
            self._active_bindings.pop(vdom_key, None)
            
            logger.debug(f"Unregistered binding: {vdom_key}")
    
    def clear_all_bindings(self) -> None:
        """Clear all bindings for this renderer context."""
        with self.lock:
            # Remove from global registry
            for vdom_key in list(self._active_bindings.keys()):
                self._registry.remove_by_key(self.backend_target, vdom_key)
            
            # Clear local bindings
            self._active_bindings.clear()
            
            logger.debug(f"Cleared all bindings for {self.backend_target}")
    
    def get_binding_stats(self) -> dict[str, Any]:
        """Get statistics about the current bindings.
        
        Returns
        -------
        dict[str, Any]
            Binding statistics.
        """
        with self.lock:
            return {
                "backend_target": str(self.backend_target),
                "active_bindings": len(self._active_bindings),
                "global_stats": self._registry.get_stats()
            }


class VDOMBindingIntegrator:
    """Main integrator for VDOM bindings with rendering systems."""
    
    def __init__(self) -> None:
        """Initialize the VDOM binding integrator."""
        self._lock = threading.RLock()
        self._contexts: dict[BackendTarget, RendererBindingContext] = {}
        logger.debug("VDOM Binding Integrator initialized")
    
    def get_renderer_context(self, backend_target: BackendTarget, renderer_instance: Any = None) -> RendererBindingContext:
        """Get or create a binding context for a renderer.
        
        Parameters
        ----------
        backend_target : BackendTarget
            The type of renderer.
        renderer_instance : Any, optional
            The renderer instance.
            
        Returns
        -------
        RendererBindingContext
            The binding context for the renderer.
        """
        with self._lock:
            if backend_target not in self._contexts:
                self._contexts[backend_target] = RendererBindingContext(backend_target, renderer_instance)
            return self._contexts[backend_target]
    
    def apply_patches_with_bindings(self, backend_target: BackendTarget, patches: list[Patch]) -> None:
        """Apply VDOM patches while managing bindings.
        
        Parameters
        ----------
        backend_target : BackendTarget
            The renderer type.
        patches : list[Patch]
            The patches to apply.
        """
        context = self.get_renderer_context(backend_target)
        
        with context.lock:
            logger.debug(f"Applying {len(patches)} patches with binding management")
            
            for patch in patches:
                if patch.patch_type.name == "ADD_NODE":
                    self._handle_add_node_patch(context, patch)
                elif patch.patch_type.name == "REMOVE_NODE":
                    self._handle_remove_node_patch(context, patch)
                elif patch.patch_type.name == "UPDATE_PROPS":
                    self._handle_update_props_patch(context, patch)
                elif patch.patch_type.name == "MOVE_NODE":
                    self._handle_move_node_patch(context, patch)
                elif patch.patch_type.name == "REPLACE_ROOT":
                    self._handle_replace_root_patch(context, patch)
    
    def _handle_add_node_patch(self, context: RendererBindingContext, patch: Patch) -> None:
        """Handle an add node patch with binding registration.
        
        Parameters
        ----------
        context : RendererBindingContext
            The binding context.
        patch : Patch
            The add node patch.
        """
        from ornata.vdom.core.host_objects import create_host_object
        if patch.key is None or patch.data is None:
            return
        
        # Create host object for the new node
        if hasattr(patch.data, 'component_name'):
            host_obj = create_host_object(
                vdom_key=patch.key,
                component_name=patch.data.component_name,
                backend_target=context.backend_target,
                vdom_node=patch.data
            )
            context.register_vdom_binding(patch.key, host_obj)

            # Attempt to attach to parent if parent info is available
            parent_key = getattr(patch.data, "parent_key", None)
            if parent_key:
                parent_obj = context.get_host_object(parent_key)
                if parent_obj is not None and hasattr(parent_obj, "add_child"):
                    try:
                        index = getattr(patch.data, "child_index", -1)
                        parent_obj.add_child(host_obj, index)
                    except Exception as e:
                        logger.error(f"Failed to attach host object {patch.key} to parent {parent_key}: {e}")
    
    def _handle_remove_node_patch(self, context: RendererBindingContext, patch: Patch) -> None:
        """Handle a remove node patch with binding cleanup.
        
        Parameters
        ----------
        context : RendererBindingContext
            The binding context.
        patch : Patch
            The remove node patch.
        """
        if patch.key is None:
            return
        
        # Get host object and clean it up
        host_obj = context.get_host_object(patch.key)
        if host_obj is not None:
            # Detach from parent if supported
            if hasattr(host_obj, "parent") and hasattr(host_obj.parent, "remove_child"):
                try:
                    host_obj.parent.remove_child(host_obj)
                except Exception as e:
                    logger.warning(f"Failed to detach host object {patch.key} from parent: {e}")

            if hasattr(host_obj, 'destroy'):
                try:
                    host_obj.destroy()
                except Exception as e:
                    logger.error(f"Error destroying host object for key {patch.key}: {e}")
        
        context.unregister_vdom_binding(patch.key)
    
    def _handle_update_props_patch(self, context: RendererBindingContext, patch: Patch) -> None:
        """Handle an update props patch.
        
        Parameters
        ----------
        context : RendererBindingContext
            The binding context.
        patch : Patch
            The update props patch.
        """
        if patch.key is None or patch.data is None:
            return
        
        # Get host object and update its properties
        host_obj = context.get_host_object(patch.key)
        if host_obj is not None and hasattr(host_obj, 'update_properties'):
            try:
                host_obj.update_properties(patch.data)
            except Exception as e:
                logger.error(f"Error updating properties for key {patch.key}: {e}")
    
    def _handle_move_node_patch(self, context: RendererBindingContext, patch: Patch) -> None:
        """Handle a move node patch.
        
        Parameters
        ----------
        context : RendererBindingContext
            The binding context.
        patch : Patch
            The move node patch.
        """
        if patch.key is None:
            return
        
        host_obj = context.get_host_object(patch.key)
        if host_obj is None:
            logger.warning(f"Cannot move node {patch.key}: Host object not found")
            return

        new_index = patch.data
        
        # Attempt to move the node using standard host object protocols
        moved = False
        
        # Strategy 1: Parent-based move
        if hasattr(host_obj, "parent") and hasattr(host_obj.parent, "move_child"):
            try:
                host_obj.parent.move_child(host_obj, new_index)
                moved = True
            except Exception as e:
                logger.warning(f"Parent-based move failed for {patch.key}: {e}")

        # Strategy 2: Self-based index update
        if not moved and hasattr(host_obj, "set_child_index"):
            try:
                host_obj.set_child_index(new_index)
                moved = True
            except Exception as e:
                logger.warning(f"Self-based index update failed for {patch.key}: {e}")

        if not moved:
            logger.debug(f"Host object for {patch.key} does not support move operations (index: {new_index})")
    
    def _handle_replace_root_patch(self, context: RendererBindingContext, patch: Patch) -> None:
        """Handle a replace root patch.
        
        Parameters
        ----------
        context : RendererBindingContext
            The binding context.
        patch : Patch
            The replace root patch.
        """
        from ornata.vdom.core.host_objects import create_host_object
        if patch.data is None:
            return
        
        # Clear all existing bindings
        context.clear_all_bindings()
        
        # Re-register the new root if it's a VDOM node
        if hasattr(patch.data, 'component_name') and patch.data.key:
            host_obj = create_host_object(
                vdom_key=patch.data.key,
                component_name=patch.data.component_name,
                backend_target=context.backend_target,
                vdom_node=patch.data
            )
            context.register_vdom_binding(patch.data.key, host_obj)
    
    def get_host_object_by_renderer(self, backend_target: BackendTarget, vdom_key: str) -> Any | None:
        """Get a host object by renderer type and VDOM key.
        
        Parameters
        ----------
        backend_target : BackendTarget
            The renderer type.
        vdom_key : str
            The VDOM key.
            
        Returns
        -------
        StandardHostObject | None
            The host object if found, None otherwise.
        """
        context = self.get_renderer_context(backend_target)
        return context.get_host_object(vdom_key)
    
    def route_event_to_vdom(self, backend_target: BackendTarget, vdom_key: str, event_type: str, event_data: dict[str, Any]) -> bool:
        """Route an event from renderer to VDOM.
        
        Parameters
        ----------
        backend_target : BackendTarget
            The renderer type.
        vdom_key : str
            The VDOM key.
        event_type : str
            The type of event.
        event_data : dict[str, Any]
            Event data.
            
        Returns
        -------
        bool
            True if the event was handled, False otherwise.
        """
        host_obj = self.get_host_object_by_renderer(backend_target, vdom_key)
        if host_obj is not None and hasattr(host_obj, 'handle_event'):
            return host_obj.handle_event(event_type, event_data)
        return False
    
    def get_integrated_stats(self) -> dict[str, Any]:
        """Get statistics about all integrated bindings.
        
        Returns
        -------
        dict[str, Any]
            Integrated binding statistics.
        """
        with self._lock:
            stats: dict[str, int | dict[str, Any]] = {
                "contexts": {},
                "total_active_bindings": 0
            }
            
            for backend_target, context in self._contexts.items():
                context_stats: dict[str, Any] = context.get_binding_stats()
                stats["contexts"][str(backend_target)] = context_stats
                stats["total_active_bindings"] += context_stats["active_bindings"]
            
            return stats


# Global integrator instance
_integrator: VDOMBindingIntegrator | None = None
_integrator_lock = threading.Lock()


def get_vdom_binding_integrator() -> VDOMBindingIntegrator:
    """Get the global VDOM binding integrator instance.
    
    Returns
    -------
    VDOMBindingIntegrator
        The global integrator instance.
    """
    global _integrator
    with _integrator_lock:
        if _integrator is None:
            _integrator = VDOMBindingIntegrator()
        return _integrator


def bind_host_object_to_tree(
    backend_target: BackendTarget,
    vdom_key: str,
    host_obj: Any,
    bindings_registry: HostBindingRegistry | None = None
) -> None:
    """Bind a host object to a VDOM tree using the bindings registry.
    
    This is a convenience function for binding host objects to VDOM trees
    using the global or provided bindings registry.
    
    Parameters
    ----------
    backend_target : BackendTarget
        The type of renderer.
    vdom_key : str
        The VDOM key for the binding.
    host_obj : StandardHostObject
        The host object to bind.
    bindings_registry : HostBindingRegistry | None
        The bindings registry to use. If None, uses the global registry.
    """
    if bindings_registry is None:
        bindings_registry = get_bindings_registry()
    
    bindings_registry.register_bind(backend_target, vdom_key, host_obj)
    logger.debug(f"Bound host object to tree: {backend_target}:{vdom_key}")