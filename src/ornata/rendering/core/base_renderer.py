"""Core render interfaces used by concrete renderers.

This module replaces the legacy `ornata.renderers.base` placement with a
minimal, focused contract under `ornata.rendering.core`.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ornata.api.exports.definitions import BackendTarget, GuiNode, MeasureProtocol, RenderOutput


class RenderableBase:
    """Base class for components that render to strings."""

    def render(self) -> str | Iterable[str] | None:
        """Render the component to console output.
        
        Returns
        -------
        str | Iterable[str] | None
            The rendered content.
        """
        raise NotImplementedError

    def to_node(self) -> GuiNode:
        """Convert renderable to a GUI node.
        
        Returns
        -------
        GuiNode
            The GUI node representation.
        """
        from ornata.api.exports.definitions import GuiNode
        component_name = getattr(self, "component_name", self.__class__.__name__.lower())

        rendered = self.render()
        text_content: str | None
        if isinstance(rendered, str):
            text_content = rendered
        elif isinstance(rendered, Iterable):
            text_content = "".join(str(chunk) for chunk in rendered)
        else:
            text_content = None

        measurement = self.measure()

        node = GuiNode(component_name=component_name, text=text_content)
        node.metadata["renderable"] = self

        if measurement is not None:
            node.width = measurement.width
            node.height = measurement.height

        return node

    def measure(self) -> MeasureProtocol | None:
        """Measure the component dimensions.
        
        Returns
        -------
        MeasureProtocol | None
            The measured dimensions or None.
        """
        rendered = self.render()
        if rendered is None:
            # Create a simple measure result
            class NullMeasure:
                width = 0
                height = 0
                
                @classmethod
                def from_text(cls, text: str) -> MeasureProtocol:
                    return cls()
            
            return NullMeasure()
        if isinstance(rendered, str):
            # Create a simple measure from text
            class TextMeasure:
                width: int
                height: int
                
                def __init__(self, text: str) -> None:
                    lines = text.split('\n')
                    self.width = max(len(line) for line in lines) if lines else 0
                    self.height = len(lines)
                
                @classmethod
                def from_text(cls, text: str) -> MeasureProtocol:
                    return cls(text)
            
            return TextMeasure(rendered)
        return TextMeasure("".join(rendered))


class Renderer:
    """Abstract renderer contract with VDOM integration.

    Concrete implementations should implement `render_tree` and
    `apply_patches` to support full and incremental rendering.
    VDOM integration is supported through optional methods.
    """

    def __init__(self, backend_target: BackendTarget) -> None:
        self.backend_target = backend_target
        self._last_output: RenderOutput | None = None
        self._vdom_bridge: Any | None = None

    def render_tree(self, tree: Any, layout_result: Any) -> RenderOutput:
        """# Render a VDOM tree with an associated layout result.

        ## Parameters

        tree : Any
            Tree structure representing components to render.
            Can be VDOMTree, GuiNode, or other renderer-specific format.
        layout_result : Any
            Computed layout for the given tree.

        ----------

        ## Returns
        RenderOutput
            The output produced by this renderer.
        """
        raise NotImplementedError("Subclasses must implement render_tree method")

    def apply_patches(self, patches: list[Any]) -> None:
        """# Apply patches to the renderer's current state.

        ## Parameters

        patches : list[Any]
            Patches describing incremental changes.
        """
        raise NotImplementedError("Subclasses must implement apply_patches method")

    # Optional VDOM integration methods - override if needed
    def render_vdom_tree(self, vdom_tree: Any, layout_result: Any | None = None) -> RenderOutput:
        """# Render a VDOM tree directly.
        
        Default implementation converts VDOM to compatible format and calls render_tree.
        
        ## Parameters
        vdom_tree : Any
            VDOM tree to render.
        layout_result : Any | None
            Optional layout result.
            
        ## Returns
        RenderOutput
            Rendered output.
        """
        # Try to convert VDOM tree to renderer format
        converted_tree = self._convert_vdom_to_renderer_format(vdom_tree)
        return self.render_tree(converted_tree, layout_result)

    def apply_vdom_patches(self, patches: list[Any]) -> None:
        """# Apply VDOM patches to the renderer.
        
        Default implementation attempts to use existing apply_patches method.
        
        ## Parameters
        patches : list[Any]
            VDOM patches to apply.
        """
        # Try to apply patches using existing interface
        if hasattr(self, 'apply_patches'):
            self.apply_patches(patches)

    def _convert_vdom_to_renderer_format(self, vdom_tree: Any) -> Any:
        """# Convert VDOM tree to renderer-specific format.
        
        Subclasses should override this for optimal conversion.
        
        ## Parameters
        vdom_tree : Any
            VDOM tree to convert.
            
        ## Returns
        Any
            Renderer-specific tree format.
        """
        # Default implementation tries common conversions
        if hasattr(vdom_tree, 'root'):
            return vdom_tree.root
        return vdom_tree

    # Host object management for VDOM integration
    def create_host_for_node(self, node: Any) -> Any:
        """# Create a host object for a VDOM node.
        
        Default implementation returns node wrapped in a simple host.
        
        ## Parameters
        node : Any
            VDOM node to create host for.
            
        ## Returns
        Any
            Host object representation.
        """
        return node

    def apply_props_to_host(self, host: Any, props: dict[str, Any]) -> None:
        """Apply properties to a host object.
        
        Default implementation logs the props application.
        
        Parameters
        ----------
        host : Any
            Host object to update.
        props : dict[str, Any]
            Properties to apply.
        """
        # Default: no-op for renderer compatibility
        pass

    def move_host(self, host: Any, position: int) -> None:
        """Move a host object to a new position.
        
        Default implementation logs the move.
        
        Parameters
        ----------
        host : Any
            Host object to move.
        position : int
            New position.
        """
        # Default: no-op for renderer compatibility
        pass

    def get_current_output(self) -> RenderOutput | None:
        """Return the most recent output if available.

        Returns
        -------
        RenderOutput | None
            Last output or None when not rendered yet.
        """
        return self._last_output

    # Helper for subclasses to persist last output
    def _set_last_output(self, output: RenderOutput) -> RenderOutput:
        self._last_output = output
        return output
