"""CLI-specific VDOM adapter for terminal rendering.

This module provides VDOM-to-CLI adapter implementation that translates
VDOM tree structures into CLI-specific rendering primitives.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import BackendTarget, Patch, PatchType, VDOMNode, VDOMTree
from ornata.api.exports.utils import get_logger
from ornata.rendering.adapters.base import VDOMAdapter
from ornata.styling.colorkit.resolver import ColorResolver

if TYPE_CHECKING:
    from ornata.api.exports.definitions import StandardHostObject
    from ornata.definitions.dataclasses.styling import BackendStylePayload

logger = get_logger(__name__)


class CLIAdapter(VDOMAdapter):
    """VDOM adapter for CLI rendering.
    
    This adapter translates VDOM tree structures into CLI-specific primitives
    while maintaining VDOM diffing and patch application benefits.
    Integrates with the ornata.styling system for proper styling resolution.
    """
    
    def __init__(self, backend_target: BackendTarget, renderer_instance: Any) -> None:
        """Initialize the CLI adapter.
        
        Parameters
        ----------
        backend_target : BackendTarget
            The type of renderer (must be CLI).
        renderer_instance : CLIRenderer
            The CLI renderer instance.
        """
        if backend_target != BackendTarget.CLI:
            raise ValueError(f"CLIAdapter can only handle CLI renderer, got {backend_target}")
        
        super().__init__(backend_target, renderer_instance)
        self._styling_enabled = True
        self._color_resolver = ColorResolver()
        logger.debug("CLI adapter initialized")
    
    def _do_initialize(self) -> None:
        """Initialize CLI-specific resources."""
        # CLI-specific initialization can be added here
        logger.debug("CLI adapter resources initialized")
    
    def convert_tree(self, vdom_tree: VDOMTree) -> Any:
        """Convert a VDOM tree to CLI-compatible format.
        
        For the cell-based renderer, this returns the GuiNode tree from runtime
        which contains proper layout and styling metadata.
        
        Parameters
        ----------
        vdom_tree : VDOMTree
            The VDOM tree to convert.
            
        Returns
        -------
        Any
            GuiNode tree for cell-based rendering, or text for fallback.
        """
        # Try to get the GuiNode tree from runtime which has proper styling metadata
        from ornata.core.runtime import OrnataRuntime
        
        # Access the runtime's last_gui_tree if available
        # This is a bit of a hack - ideally the runtime would pass the tree directly
        import threading
        _runtime_storage: dict[str, Any] = getattr(threading.local(), '_ornata_runtime', None) or {}
        gui_tree = _runtime_storage.get('last_gui_tree')
        
        if gui_tree is not None:
            return gui_tree
        
        # Fallback to text conversion for backward compatibility
        if vdom_tree.root is None:
            return ""
        return self._convert_node_to_text(vdom_tree.root)
    
    def convert_node(self, node: VDOMNode) -> str:
        """Convert a VDOM node to CLI text format.
        
        Parameters
        ----------
        node : VDOMNode
            The VDOM node to convert.
            
        Returns
        -------
        str
            CLI-formatted text representation.
        """
        return self._convert_node_to_text(node)
    
    def apply_patches(self, patches: list[Patch]) -> None:
        """Apply VDOM patches to the CLI renderer.
        
        Parameters
        ----------
        patches : list[Patch]
            VDOM patches to apply.
        """
        with self.context._lock:
            logger.debug(f"Applying {len(patches)} patches to CLI renderer")
            
            for patch in patches:
                if patch.patch_type == PatchType.ADD_NODE:
                    self._apply_add_node_patch(patch)
                elif patch.patch_type == PatchType.REMOVE_NODE:
                    self._apply_remove_node_patch(patch)
                elif patch.patch_type == PatchType.UPDATE_PROPS:
                    self._apply_update_props_patch(patch)
                elif patch.patch_type == PatchType.MOVE_NODE:
                    self._apply_move_node_patch(patch)
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
                caps=self._get_cli_capabilities(),
                backend=BackendTarget.CLI,
            )
        except Exception as e:
            logger.debug(f"Failed to resolve backend style for node {node.component_name}: {e}")
            return None
    
    def _get_cli_capabilities(self) -> dict[str, Any]:
        """Get CLI capabilities for style resolution.
        
        Returns
        -------
        dict[str, Any]
            CLI capability descriptor.
        """
        # This could be enhanced to detect actual CLI capabilities
        return {
            "color_depth": "C16",  # CLI typically supports 16 colors
            "dpi": 96,  # Default DPI
            "cell_metrics": lambda: (10, 16),  # Default cell width/height
        }
    
    def _convert_node_to_text(self, node: VDOMNode) -> str:
        """Convert a VDOM node tree to CLI text with styling."""
        
        props = node.props
        backend_payload = self._resolve_backend_style_for_node(node)
        resolved_style = backend_payload.style if backend_payload else None
        
        # Handle different component types with styling
        if content := props.get("content"):
            if hasattr(content, "title") and content.title:
                text = str(content.title)
                if hasattr(content, "subtitle") and content.subtitle:
                    text += "\n" + str(content.subtitle)
                if resolved_style and self._styling_enabled:
                    text = self._apply_style_to_text(text, backend_payload)
                return text
        
        # Handle table data
        columns = props.get("columns")
        rows = props.get("rows")
        if columns and rows:
            lines: list[str] = []
            # Style headers differently
            header_line = " | ".join(str(col) for col in columns)
            if backend_payload and self._styling_enabled:
                header_line = self._apply_style_to_text(header_line, backend_payload)
            lines.append(header_line)
            lines.append("-" * len(header_line.replace("\033[", "").replace("m", "")))  # Adjust for ANSI codes
            
            for row in rows:
                row_line = " | ".join(str(cell) for cell in row)
                lines.append(row_line)
            return "\n".join(lines)
        
        # Handle button text with styling
        if content and hasattr(content, "text") and content.text:
            button_text = f"[{content.text}]"
            if backend_payload and self._styling_enabled:
                button_text = self._apply_style_to_text(button_text, backend_payload)
            return button_text
        
        # Handle input placeholder with actual value and cursor
        if content and hasattr(content, "placeholder") and content.placeholder:
            # Get the actual value from props if available
            value = props.get("value", "")
            
            # Show typed value or placeholder
            display_text = value if value else content.placeholder
            
            # Check if this input is focused via context (we'll need to pass this through)
            is_focused = props.get("focused", False)
            if is_focused:
                display_text += "_"
            
            input_text = f"[{display_text}]"
            if backend_payload and self._styling_enabled:
                input_text = self._apply_style_to_text(input_text, backend_payload)
            return input_text
        
        # Handle text content
        if text_content := props.get("content"):
            if isinstance(text_content, str):
                if backend_payload and self._styling_enabled:
                    return self._apply_style_to_text(text_content, backend_payload)
                return text_content
        
        # Process children
        text_parts: list[str] = []
        for child in node.children:
            child_text = self._convert_node_to_text(child)
            if child_text:
                text_parts.append(child_text)
        
        result = "\n".join(text_parts) if text_parts else f"[{node.component_name}]"
        
        # Apply styling to the result if available
        if backend_payload and self._styling_enabled and not text_parts:
            result = self._apply_style_to_text(result, backend_payload)
        
        return result

    def _apply_style_to_text(self, text: str, backend_payload: BackendStylePayload) -> str:
        """Apply resolved style to text content.
        
        Parameters
        ----------
        text : str
            Text content to style.
        backend_payload : BackendStylePayload
            Backend-conditioned styling bundle.
            
        Returns
        -------
        str
            Styled text.
        """
        styled_text = text
        resolved_style = backend_payload.style

        if not resolved_style:
            return styled_text

        fg_code = (
            resolved_style.color
            if isinstance(resolved_style.color, str) and resolved_style.color.startswith("\033[")
            else self._color_resolver.resolve_ansi(resolved_style.color)
        )
        bg_code = (
            resolved_style.background
            if isinstance(resolved_style.background, str) and resolved_style.background.startswith("\033[")
            else self._color_resolver.resolve_background(
                str(resolved_style.background) if resolved_style.background else None
            )
        )

        prefix = ""
        if fg_code:
            prefix += fg_code
        if bg_code:
            prefix += bg_code

        if prefix:
            return f"{prefix}{styled_text}\033[0m"
        return styled_text
    
    def _apply_add_node_patch(self, patch: Patch) -> None:
        """Apply an add node patch.
        
        Parameters
        ----------
        patch : Patch
            The add node patch to apply.
        """
        if patch.key is None or patch.data is None:
            return
        
        new_node = patch.data
        if isinstance(new_node, VDOMNode):
            # Create renderer representation
            renderer_obj = self.convert_node(new_node)
            
            # Register the mapping
            self.context.register_node_mapping(patch.key, renderer_obj)
            
            # Create and register host object
            host_obj = self.create_host_object(new_node)
            self.context.register_host_object(patch.key, host_obj)
            
            logger.debug(f"CLI: Added node {patch.key} ({new_node.component_name})")
    
    def _apply_remove_node_patch(self, patch: Patch) -> None:
        """Apply a remove node patch.
        
        Parameters
        ----------
        patch : Patch
            The remove node patch to apply.
        """
        if patch.key is None:
            return
        
        # Remove from mappings
        self.context.node_mapping.pop(patch.key, None)
        self.context.host_objects.pop(patch.key, None)
        
        logger.debug(f"CLI: Removed node {patch.key}")
    
    def _apply_update_props_patch(self, patch: Patch) -> None:
        """Apply an update props patch.
        
        Parameters
        ----------
        patch : Patch
            The update props patch to apply.
        """
        if patch.key is None or patch.data is None:
            return
        
        # Get existing host object
        host = self.context.get_host_object(patch.key)
        if host is not None:
            # Apply props to host
            self.apply_props_to_host(host, patch.data)
            logger.debug(f"CLI: Updated props for node {patch.key}: {list(patch.data.keys())}")
    
    def _apply_move_node_patch(self, patch: Patch) -> None:
        """Apply a move node patch.
        
        Parameters
        ----------
        patch : Patch
            The move node patch to apply.
        """
        if patch.key is None:
            return
        
        # For CLI, node movement typically means reordering for text output
        logger.debug(f"CLI: Moved node {patch.key} to position {patch.data}")
    
    def _apply_replace_root_patch(self, patch: Patch) -> None:
        """Apply a replace root patch.
        
        Parameters
        ----------
        patch : Patch
            The replace root patch to apply.
        """
        if patch.data is None:
            return
        
        # Clear all mappings
        with self.context._lock:
            self.context.node_mapping.clear()
            self.context.host_objects.clear()
        
        new_root = patch.data
        if isinstance(new_root, VDOMNode):
            # Re-register the new root
            root_key = "root"
            self.context.register_node_mapping(root_key, self.convert_node(new_root))
            
            # Create and register host object for root
            host_obj = self.create_host_object(new_root)
            self.context.register_host_object(root_key, host_obj)
            
            logger.debug("CLI: Replaced root node")
    
    def create_host_object(self, node: VDOMNode) -> StandardHostObject:
        """Create a CLI-specific host object for a VDOM node.
        
        Parameters
        ----------
        node : VDOMNode
            The VDOM node to create host for.
            
        Returns
        -------
        StandardHostObject
            CLI-specific host object.
        """
        from ornata.api.exports.definitions import StandardHostObject
        
        return StandardHostObject(
            vdom_key=node.key or "unknown",
            component_name=node.component_name,
            backend_target=self.backend_target,
        )