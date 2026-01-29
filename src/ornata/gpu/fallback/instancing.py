"""CPU-based software instancing for geometry rendering fallback."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ornata.api.exports.definitions import InstanceTransform

if TYPE_CHECKING:
    from ornata.gpu.misc import Geometry


class CPUInstancer:
    """CPU-based instancing processor for software rendering fallback.

    Handles processing of instance data to create expanded geometry
    by duplicating and transforming base geometry for each instance.
    """

    def process_instances(self, base_geometry: Geometry, instance_data: list[float], instance_count: int) -> Geometry:
        """Process instance data and create expanded geometry with all instances applied.

        Args:
            base_geometry: The base geometry to instance.
            instance_data: Flattened list of instance transform data (x, y, scale_x, scale_y, rotation per instance).
            instance_count: Number of instances to render.

        Returns:
            Expanded geometry containing all transformed instances.

        Raises:
            ValueError: If instance_data length does not match expected size.
        """
        # Validate instance data length (5 floats per instance: x, y, scale_x, scale_y, rotation)
        expected_length = instance_count * 5
        if len(instance_data) != expected_length:
            raise ValueError(f"Instance data length {len(instance_data)} does not match expected {expected_length} for {instance_count} instances")

        expanded_vertices: list[float] = []
        expanded_indices: list[int] = []
        vertex_offset = 0

        # Process each instance
        for i in range(instance_count):
            # Extract transform data for this instance
            start_idx = i * 5
            transform_data = instance_data[start_idx:start_idx + 5]
            transform = InstanceTransform(*transform_data)

            # Apply transform to base geometry vertices
            transformed_vertices = self._apply_transform(base_geometry.vertices, transform)
            expanded_vertices.extend(transformed_vertices)

            # Adjust indices for vertex offset and extend
            adjusted_indices = [idx + vertex_offset for idx in base_geometry.indices]
            expanded_indices.extend(adjusted_indices)

            # Update vertex offset for next instance
            vertex_offset += len(transformed_vertices) // 5  # 5 floats per vertex
        from ornata.api.exports.definitions import Geometry
        return Geometry(
            vertices=expanded_vertices,
            indices=expanded_indices,
            vertex_count=len(expanded_vertices) // 5,
            index_count=len(expanded_indices)
        )

    def _apply_transform(self, vertices: list[float], transform: InstanceTransform) -> list[float]:
        """Apply instance transform to a set of vertices.

        Args:
            vertices: Base vertex data (x, y, z, u, v per vertex).
            transform: Transform to apply.

        Returns:
            Transformed vertex data.
        """
        transformed: list[float] = []

        # Process vertices in groups of 5 (x, y, z, u, v)
        for i in range(0, len(vertices), 5):
            vx, vy, vz, vu, vv = vertices[i:i + 5]

            # Apply scaling
            vx *= transform.scale_x
            vy *= transform.scale_y

            # Apply rotation
            cos_r = math.cos(transform.rotation)
            sin_r = math.sin(transform.rotation)
            new_vx = vx * cos_r - vy * sin_r
            new_vy = vx * sin_r + vy * cos_r
            vx, vy = new_vx, new_vy

            # Apply translation
            vx += transform.x
            vy += transform.y

            transformed.extend([vx, vy, vz, vu, vv])

        return transformed


__all__ = ["CPUInstancer"]