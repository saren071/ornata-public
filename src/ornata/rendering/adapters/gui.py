"""GUI-specific VDOM adapter for graphical user interface rendering.

This module provides VDOM-to-GUI adapter implementation that translates
VDOM tree structures into GUI-specific rendering primitives.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import BackendTarget, Patch, PatchType, VDOMNode, VDOMTree
from ornata.api.exports.utils import get_logger
from ornata.rendering.adapters.base import VDOMAdapter

if TYPE_CHECKING:
    from ornata.api.exports.definitions import StandardHostObject
    from ornata.definitions.dataclasses.styling import BackendStylePayload

logger = get_logger(__name__)


class GUIAdapter(VDOMAdapter):
    """VDOM adapter for GUI rendering.
    
    This adapter translates VDOM tree structures into GUI-specific primitives
    (GuiNode trees) while maintaining VDOM diffing and patch application benefits.
    """
    
    def __init__(self, backend_target: BackendTarget, renderer_instance: Any) -> None:
        if backend_target != BackendTarget.GUI:
            raise ValueError(f"GUIAdapter can only handle GUI renderer, got {backend_target}")
        super().__init__(backend_target, renderer_instance)
        self._styling_enabled = True
        logger.debug("GUI adapter initialized")
    
    def _do_initialize(self) -> None:
        """Initialize GUI-specific resources."""
        # Ensure the renderer instance is ready
        if hasattr(self.renderer_instance, "initialize"):
            self.renderer_instance.initialize()
    
    def convert_tree(self, vdom_tree: VDOMTree) -> Any:
        """Convert a VDOM tree to GUI node structure."""
        if vdom_tree.root is None:
            return None
        return self._convert_node_to_gui(vdom_tree.root)
    
    def convert_node(self, node: VDOMNode) -> Any:
        """Convert a VDOM node to GUI format."""
        return self._convert_node_to_gui(node)
    
    def apply_patches(self, patches: list[Patch]) -> None:
        """Apply VDOM patches to the GUI renderer adapter state."""
        with self.context._lock:
            for patch in patches:
                if patch.patch_type == PatchType.ADD_NODE:
                    self._apply_add_node_patch(patch)
                elif patch.patch_type == PatchType.REMOVE_NODE:
                    self._apply_remove_node_patch(patch)
                elif patch.patch_type == PatchType.UPDATE_PROPS:
                    self._apply_update_props_patch(patch)
                elif patch.patch_type == PatchType.REPLACE_ROOT:
                    self._apply_replace_root_patch(patch)
    
    def _resolve_backend_style_for_node(self, node: VDOMNode) -> BackendStylePayload | None:
        """Resolve backend-conditioned style for a VDOM node using the styling system."""
        if not self._styling_enabled:
            return None

        try:
            from ornata.styling.runtime import resolve_backend_component_style

            component_name = node.component_name
            state = node.props.get("state", {})
            theme_overrides = node.props.get("theme_overrides", {})

            return resolve_backend_component_style(
                component_name=component_name,
                state=state,
                theme_overrides=theme_overrides,
                caps=self._get_gui_capabilities(),
                backend=BackendTarget.GUI,
            )
        except Exception as e:
            logger.debug(f"Failed to resolve backend style for node {node.component_name}: {e}")
            return None
    
    def _get_gui_capabilities(self) -> dict[str, Any]:
        return {
            "color_depth": "TRUECOLOR",
            "dpi": 96,
            "cell_metrics": lambda: (10, 16),
            "font_metrics": lambda: (12, 16),
        }
    
    def _convert_node_to_gui(self, node: VDOMNode) -> Any:
        """Convert a VDOM node to GuiNode."""
        from ornata.api.exports.definitions import GuiNode

        # Create GUI node
        gui_node = GuiNode(
            component_name=node.component_name,
            text=node.props.get("content", None) if isinstance(node.props.get("content"), str) else None
        )
        
        # Map layout properties directly
        gui_node.x = node.props.get("x", 0)
        gui_node.y = node.props.get("y", 0)
        gui_node.width = node.props.get("width", 0)
        gui_node.height = node.props.get("height", 0)
        
        # Resolve and attach style using backend-aware pipeline
        backend_payload = self._resolve_backend_style_for_node(node)
        if backend_payload and self._styling_enabled:
            # Use renderer metadata from the styling pipeline directly
            style_attrs = backend_payload.renderer_metadata
            style_attrs["resolved_style"] = backend_payload.style

            # Store style attributes in GUI node metadata for the renderer to use
            gui_node.metadata.update(style_attrs)
            gui_node.metadata["backend_payload"] = backend_payload

            # Also attach as a direct attribute if the renderer expects it
            gui_node.style = backend_payload.style
        
        # Convert children
        for child in node.children:
            child_gui = self._convert_node_to_gui(child)
            if child_gui is not None:
                gui_node.children.append(child_gui)
        
        # Store VDOM key
        if node.key:
            gui_node.metadata["vdom_key"] = node.key
        
        return gui_node
    
    def _apply_add_node_patch(self, patch: Patch) -> None:
        if patch.key is None or patch.data is None:
            return

        new_node = patch.data
        if isinstance(new_node, VDOMNode):
            renderer_obj = self.convert_node(new_node)
            self.context.register_node_mapping(patch.key, renderer_obj)
            host_obj = self.create_host_object(new_node)
            self.context.register_host_object(patch.key, host_obj)
    
    def _apply_remove_node_patch(self, patch: Patch) -> None:
        if patch.key is None:
            return
        self.context.node_mapping.pop(patch.key, None)
        self.context.host_objects.pop(patch.key, None)
    
    def _apply_update_props_patch(self, patch: Patch) -> None:
        if patch.key is None or patch.data is None:
            return
        host = self.context.get_host_object(patch.key)
        if host is not None:
            self.apply_props_to_host(host, patch.data)
    
    def _apply_replace_root_patch(self, patch: Patch) -> None:
        if patch.data is None:
            return
        with self.context._lock:
            self.context.node_mapping.clear()
            self.context.host_objects.clear()
        
        new_root = patch.data
        if isinstance(new_root, VDOMNode):
            root_key = "root"
            self.context.register_node_mapping(root_key, self.convert_node(new_root))
            host_obj = self.create_host_object(new_root)
            self.context.register_host_object(root_key, host_obj)
    
    def create_host_object(self, node: VDOMNode) -> StandardHostObject:
        from ornata.rendering.adapters.base import StandardHostObject
        return StandardHostObject(
            vdom_key=node.key or "unknown",
            component_name=node.component_name,
            backend_target=self.backend_target,
        )