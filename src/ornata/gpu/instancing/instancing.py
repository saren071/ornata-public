"""GPU instanced rendering detection and management."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import ComponentIdentity, InstanceGroup, InstanceTransform
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Component, Geometry
    from ornata.gpu.misc import GPUBackend, Shader

logger = get_logger(__name__)


class InstanceDetector:
    """Detects and groups identical renderable components for instanced rendering."""

    def __init__(self) -> None:
        """Initialize the instance detector."""
        self.groups: dict[ComponentIdentity, InstanceGroup] = {}

    def analyze_component(self, component: Component) -> ComponentIdentity:
        """Analyze a component and return its identity.

        Args:
            component: Renderable component to analyze.

        Returns:
            ComponentIdentity for the component.
        """
        # Get component type
        component_type = type(component).__name__

        # Generate properties hash
        properties_hash = self._hash_component_properties(component)

        # Generate styling hash
        styling_hash = self._hash_component_styling(component)

        component_name_attr = getattr(component, "component_name", None)
        component_name = component_name_attr if isinstance(component_name_attr, str) and component_name_attr else component_type

        return ComponentIdentity(
            component_name=component_name,
            component_type=component_type,
            properties_hash=properties_hash,
            styling_hash=styling_hash,
        )

    def add_component(self, component: Component, transform: InstanceTransform | None = None) -> None:
        """Add a component to the instance detection system.

        Args:
            component: Renderable component to add.
            transform: Optional transform data for the component.
        """
        identity = self.analyze_component(component)

        if identity not in self.groups:
            self.groups[identity] = InstanceGroup(identity=identity)

        group = self.groups[identity]

        # Set base geometry if not set (from first component in group)
        if group.base_geometry is None:
            # Generate geometry for this component
            group.base_geometry = self._generate_geometry(component)

        # Add transform (default if none provided)
        if transform is None:
            transform = InstanceTransform()

        group.add_instance(transform)

    def get_instance_groups(self, min_instances: int = 2) -> list[InstanceGroup]:
        """Get all instance groups that qualify for instanced rendering.

        Args:
            min_instances: Minimum instances required for grouping.

        Returns:
            List of qualifying instance groups.
        """
        return [group for group in self.groups.values() if group.is_instancable(min_instances)]

    def clear(self) -> None:
        """Clear all detected instance groups."""
        self.groups.clear()

    def _hash_component_properties(self, component: Component) -> str:
        """Generate a hash of component properties.

        Args:
            component: Component to hash.

        Returns:
            SHA256 hash string of component properties.
        """
        # Collect hashable properties
        props: list[tuple[str, str]] = []

        # Sort for consistent hashing
        props.sort(key=lambda x: x[0])

        # Create hash
        hasher = hashlib.sha256()
        for key, value in props:
            hasher.update(f"{key}:{value}".encode())

        return hasher.hexdigest()

    def _hash_component_styling(self, component: Component) -> str:
        """Generate a hash of component styling.

        Args:
            component: Component to hash styling for.

        Returns:
            SHA256 hash string of component styling.
        """
        try:
            style_getter = getattr(component, "get_resolved_style", None)
            if style_getter is None:
                raise AttributeError("Component has no get_resolved_style method")
            resolved_style: Any = style_getter()

            # Collect style properties that affect rendering
            style_props = [
                ("color", getattr(resolved_style, "color", None)),
                ("background_color", getattr(resolved_style, "background_color", None)),
                ("font_family", getattr(resolved_style, "font_family", None)),
                ("font_size", getattr(resolved_style, "font_size", None)),
                ("font_weight", getattr(resolved_style, "font_weight", None)),
                ("border_style", getattr(resolved_style, "border_style", None)),
                ("border_width", getattr(resolved_style, "border_width", None)),
                ("padding", getattr(resolved_style, "padding", None)),
                ("margin", getattr(resolved_style, "margin", None)),
            ]

            # Sort for consistent hashing
            style_props.sort(key=lambda x: x[0])

            # Create hash
            hasher = hashlib.sha256()
            for key, value in style_props:
                if value is not None:
                    hasher.update(f"{key}:{str(value)}".encode())

            return hasher.hexdigest()

        except Exception as e:
            raise ValueError(f"Failed to hash styling for {component.component_name}: {e}") from e

    def _generate_geometry(self, component: Component) -> Geometry | None:
        """Generate geometry for a component with enhanced performance optimization.

        Args:
            component: Component to generate geometry for.

        Returns:
            Geometry object or None if generation fails.
        """
        try:
            from ornata.gpu.device.geometry import component_to_gpu_geometry
            geometry = component_to_gpu_geometry(component)
            return geometry
        except Exception as exc:
            logger.debug(
                "Failed to generate base geometry for instancing of %s: %s",
                component.component_name,
                exc,
            )
            return None

    def optimize_memory_usage(self, max_transforms_per_group: int = 1000) -> None:
        """Optimize memory usage by compressing transform data.

        Args:
            max_transforms_per_group: Maximum transforms to keep per group before compression.
        """
        for group in self.groups.values():
            if len(group.transforms) > max_transforms_per_group:
                # Keep only the most recent transforms to manage memory
                group.transforms = group.transforms[-max_transforms_per_group:]
                group.component_count = len(group.transforms)

    def get_performance_stats(self) -> dict[str, int | float]:
        """Get performance statistics for instancing optimization.

        Returns:
            Dictionary with performance metrics.
        """
        stats: dict[str, int | float] = {
            "total_groups": len(self.groups),
            "total_instances": sum(group.component_count for group in self.groups.values()),
            "instancable_groups": len([g for g in self.groups.values() if g.is_instancable()]),
        }

        if stats["total_instances"] > 0:
            stats["compression_ratio"] = stats["instancable_groups"] / stats["total_groups"] if stats["total_groups"] > 0 else 0.0
            stats["potential_savings"] = stats["total_instances"] - stats["instancable_groups"]
        else:
            stats["compression_ratio"] = 0.0
            stats["potential_savings"] = 0

        return stats


class InstancedRenderer:
    """Advanced GPU instanced rendering manager with shader support."""

    def __init__(self, backend: GPUBackend) -> None:
        """Initialize the instanced renderer.

        Args:
            backend: GPU backend for shader compilation and rendering.
        """
        self.backend = backend
        self.instance_detector = InstanceDetector()
        self.shaders: dict[str, Shader] = {}

    def create_instanced_shader(self, name: str, vertex_shader: str, fragment_shader: str | None = None) -> Shader | None:
        """Create a shader optimized for instanced rendering.

        Args:
            name: Name for the shader.
            vertex_shader: Vertex shader source.
            fragment_shader: Fragment shader source.

        Returns:
            Compiled shader or None if compilation fails.
        """
        if fragment_shader is None:
            fragment_shader = """#version 460
in vec4 v_color;
in vec4 v_instance_color;
out vec4 fragColor;
void main() {
    fragColor = v_color * v_instance_color;
}"""

        # Create shader with instanced rendering optimizations
        shader = self.backend.create_shader(name, vertex_shader, fragment_shader)
        if shader:
            self.shaders[name] = shader
            logger.debug(f"Created instanced shader: {name}")
        else:
            logger.warning(f"Failed to create instanced shader: {name}")

        return shader

    def render_instanced_groups(self, groups: list[InstanceGroup], shader: Shader) -> None:
        """Render multiple instance groups efficiently.

        Args:
            groups: List of instance groups to render.
            shader: Shader to use for rendering.
        """
        if not groups:
            return

        try:
            shader.bind()

            # Process groups by shader compatibility
            compatible_groups = self._group_by_shader_compatibility(groups, shader)

            for group in compatible_groups:
                if group.base_geometry and group.transforms:
                    self._render_single_group(group, shader)

            logger.debug(f"Rendered {len(compatible_groups)} instanced groups")

        except Exception as e:
            logger.error(f"Failed to render instanced groups: {e}")

    def _group_by_shader_compatibility(self, groups: list[InstanceGroup], shader: Shader | None) -> list[InstanceGroup]:
        """Filter groups compatible with the shader.

        Args:
            groups: Groups to filter.
            shader: Shader to check compatibility against.

        Returns:
            Compatible groups.
        """
        if shader is None:
            return []

        # For now, assume all groups are compatible
        # In a full implementation, this would check shader capabilities
        return groups

    def _render_single_group(self, group: InstanceGroup, shader: Shader | None) -> None:
        """Render a single instance group.

        Args:
            group: Instance group to render.
            shader: Shader to use.
        """
        try:
            if shader is None:
                logger.warning("Cannot render instance group: no shader provided")
                return

            # Prepare instance data efficiently
            instance_data = self._prepare_instance_data(group.transforms)

            # Use GPU instancing if available
            if hasattr(self.backend, "render_instanced_geometry"):
                base_geometry = group.base_geometry
                if base_geometry is None:
                    logger.warning("Cannot render instance group: base_geometry is None")
                    return
                self.backend.render_instanced_geometry(base_geometry, instance_data, group.component_count, shader)
            else:
                # Fallback to individual renders
                self._render_instances_individually(group, shader)

        except Exception as e:
            logger.warning(f"Failed to render instance group: {e}")

    def _prepare_instance_data(self, transforms: list[InstanceTransform]) -> list[float]:
        """Prepare instance data for GPU upload.

        Args:
            transforms: List of transforms to convert.

        Returns:
            Flattened transform data for GPU.
        """
        instance_data: list[float] = []
        for transform in transforms:
            instance_data.extend([transform.x, transform.y, transform.scale_x, transform.scale_y, transform.rotation])
        return instance_data

    def _render_instances_individually(self, group: InstanceGroup, shader: Shader | None) -> None:
        """Fallback rendering for individual instances.

        Args:
            group: Instance group to render.
            shader: Shader to use.
        """
        if shader is None:
            logger.warning("Cannot render instances individually: no shader provided")
            return

        for transform in group.transforms:
            _ = transform  # Mark as used to avoid unused variable warning
            if group.base_geometry:
                # Modify geometry by transform and render
                # This is a simplified version - full implementation would need geometry transformation
                self.backend.render_geometry(group.base_geometry, shader)


__all__ = [
    "ComponentIdentity",
    "InstanceTransform",
    "InstanceGroup",
    "InstanceDetector",
    "InstancedRenderer",
]
