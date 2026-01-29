# Software rasterization implementation for CPU fallback.
"""Software rasterization implementation for CPU fallback."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ornata.gpu.fallback.sw_pipeline import SoftwarePipeline, SoftwareShaderProgram
    from ornata.gpu.misc import Geometry, Shader


class SoftwareRasterizer:
    """Software-based rasterization for CPU fallback.

    Implements basic rasterization algorithms including line drawing,
    triangle filling, and shader emulation.
    """

    def __init__(self, width: int = 800, height: int = 600) -> None:
        self._width = width
        self._height = height
        self._framebuffer: list[list[tuple[int, int, int, int]]] = []
        self._depth_buffer: list[list[float]] = []
        self._clear_color = (0, 0, 0, 255)
        self._lock = threading.RLock()
        self._initialize_buffers()

    def _initialize_buffers(self) -> None:
        """Initialize the framebuffer and depth buffer."""
        with self._lock:
            self._framebuffer = [[(0, 0, 0, 255) for _ in range(self._width)] for _ in range(self._height)]
            self._depth_buffer = [[float("inf") for _ in range(self._width)] for _ in range(self._height)]

    def render(self, geometry: Geometry, shader: Shader, pipeline: SoftwarePipeline, clear_depth: bool = False) -> None:
        """Perform software rendering of geometry.

        Args:
            geometry: The geometry to render.
            shader: The shader to emulate.
            pipeline: Software pipeline configuration.
            clear_depth: Whether to clear depth buffer before rendering.
        """
        with self._lock:
            if clear_depth:
                self._reset_depth_buffer()

            self._sync_viewport(pipeline)

            vertex_shader = self._resolve_vertex_shader(pipeline, shader)
            fragment_shader = self._resolve_fragment_shader(pipeline, shader)

            transformed_vertices = self._process_vertices(geometry, vertex_shader)

            # Render primitives
            if geometry.indices:
                # Indexed rendering
                self._render_indexed_triangles(transformed_vertices, geometry.indices, fragment_shader, pipeline)
            else:
                # Direct vertex rendering (assuming triangles)
                self._render_triangles(transformed_vertices, fragment_shader, pipeline)

    def _process_vertices(self, geometry: Geometry, vertex_shader: SoftwareShaderProgram | None) -> list[list[float]]:
        """Process vertices through vertex shader emulation.

        Args:
            geometry: The input geometry.
            vertex_shader: Software vertex shader program.

        Returns:
            List of transformed vertices.
        """
        transformed: list[list[float]] = []

        # Group vertices by 5 floats (x, y, z, u, v)
        for i in range(0, len(geometry.vertices), 5):
            vertex = geometry.vertices[i : i + 5]
            if len(vertex) == 5:
                if vertex_shader is not None:
                    processed = vertex_shader.emulate_vertex_shader(vertex)
                else:
                    processed = vertex
                transformed.append(processed)

        return transformed

    def _render_indexed_triangles(self, vertices: list[list[float]], indices: list[int], fragment_shader: SoftwareShaderProgram | None, pipeline: SoftwarePipeline) -> None:
        """Render indexed triangles.

        Args:
            vertices: List of vertex data.
            indices: List of vertex indices.
            fragment_shader: Fragment shader to emulate.
            pipeline: Pipeline configuration.
        """
        # Process triangles from indices
        for i in range(0, len(indices), 3):
            if i + 2 < len(indices):
                idx1, idx2, idx3 = indices[i], indices[i + 1], indices[i + 2]
                if idx1 < len(vertices) and idx2 < len(vertices) and idx3 < len(vertices):
                    v1 = vertices[idx1]
                    v2 = vertices[idx2]
                    v3 = vertices[idx3]
                    self._rasterize_triangle(v1, v2, v3, fragment_shader, pipeline)

    def _render_triangles(self, vertices: list[list[float]], fragment_shader: SoftwareShaderProgram | None, pipeline: SoftwarePipeline) -> None:
        """Render triangles directly from vertices.

        Args:
            vertices: List of vertex data.
            fragment_shader: Fragment shader to emulate.
            pipeline: Pipeline configuration.
        """
        # Process triangles (every 3 vertices)
        for i in range(0, len(vertices), 3):
            if i + 2 < len(vertices):
                v1 = vertices[i]
                v2 = vertices[i + 1]
                v3 = vertices[i + 2]
                self._rasterize_triangle(v1, v2, v3, fragment_shader, pipeline)

    def _rasterize_triangle(self, v1: list[float], v2: list[float], v3: list[float], fragment_shader: SoftwareShaderProgram | None, pipeline: SoftwarePipeline) -> None:
        """Rasterize a single triangle.

        Args:
            v1, v2, v3: Triangle vertices (x, y, z, u, v).
            fragment_shader: Fragment shader for fragment processing.
            pipeline: Pipeline configuration for depth/blend state.
        """
        # Convert to screen coordinates (simple viewport transform)
        screen_v1 = self._to_screen_coords(v1)
        screen_v2 = self._to_screen_coords(v2)
        screen_v3 = self._to_screen_coords(v3)

        # Calculate triangle bounding box
        min_x = max(0, int(min(screen_v1[0], screen_v2[0], screen_v3[0])))
        max_x = min(self._width - 1, int(max(screen_v1[0], screen_v2[0], screen_v3[0])))
        min_y = max(0, int(min(screen_v1[1], screen_v2[1], screen_v3[1])))
        max_y = min(self._height - 1, int(max(screen_v1[1], screen_v2[1], screen_v3[1])))

        # Rasterize pixels inside triangle
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                sample_x = x + 0.5
                sample_y = y + 0.5
                bary = self._barycentric_coords(sample_x, sample_y, screen_v1, screen_v2, screen_v3)
                if bary is None:
                    continue

                depth = bary[0] * v1[2] + bary[1] * v2[2] + bary[2] * v3[2]

                if not pipeline.apply_depth_test(depth, self._depth_buffer[y][x]):
                    continue

                tex_u = bary[0] * v1[3] + bary[1] * v2[3] + bary[2] * v3[3]
                tex_v = bary[0] * v1[4] + bary[1] * v2[4] + bary[2] * v3[4]

                interpolated = {
                    "position_x": sample_x,
                    "position_y": sample_y,
                    "position_z": depth,
                    "tex_u": tex_u,
                    "tex_v": tex_v,
                }

                color = self._shade_fragment(fragment_shader, interpolated)
                blended = pipeline.apply_blend_state(color, self._framebuffer[y][x])
                self._framebuffer[y][x] = blended

                if pipeline.config.depth_state.enabled and pipeline.config.depth_state.write_enabled:
                    self._depth_buffer[y][x] = depth
                elif not pipeline.config.depth_state.enabled:
                    self._depth_buffer[y][x] = depth

    def _to_screen_coords(self, vertex: list[float]) -> tuple[float, float, float, float, float]:
        """Convert vertex to screen coordinates (pixel space).

        Args:
            vertex: Vertex data (x, y, z, u, v) in pixel space where
                (0, 0) is top-left of the viewport.

        Returns:
            Screen space coordinates (x, y, z, u, v) in pixels.
        """
        x, y, z, u, v = vertex

        # Clamp to viewport bounds
        screen_x = max(0.0, min(float(self._width - 1), float(x)))
        screen_y = max(0.0, min(float(self._height - 1), float(y)))

        return (screen_x, screen_y, z, u, v)

    def _barycentric_coords(
        self,
        px: float,
        py: float,
        v1: tuple[float, float, float, float, float],
        v2: tuple[float, float, float, float, float],
        v3: tuple[float, float, float, float, float],
    ) -> tuple[float, float, float] | None:
        """Calculate barycentric coordinates.

        Args:
            px, py: Point coordinates.
            v1, v2, v3: Triangle vertices.

        Returns:
            Barycentric coordinates (w1, w2, w3) or None when outside triangle.
        """
        # Calculate areas
        area = self._triangle_area(v1, v2, v3)
        if area == 0.0:
            return None

        w1 = self._triangle_area((px, py, 0.0, 0.0, 0.0), v2, v3) / area
        w2 = self._triangle_area(v1, (px, py, 0.0, 0.0, 0.0), v3) / area
        w3 = self._triangle_area(v1, v2, (px, py, 0.0, 0.0, 0.0)) / area

        if w1 < -1e-5 or w2 < -1e-5 or w3 < -1e-5:
            return None

        return (w1, w2, w3)

    def _triangle_area(self, v1: tuple[float, float, float, float, float], v2: tuple[float, float, float, float, float], v3: tuple[float, float, float, float, float]) -> float:
        """Calculate triangle area using cross product.

        Args:
            v1, v2, v3: Triangle vertices.

        Returns:
            Triangle area.
        """
        return abs((v2[0] - v1[0]) * (v3[1] - v1[1]) - (v3[0] - v1[0]) * (v2[1] - v1[1])) * 0.5

    def _shade_fragment(self, fragment_shader: SoftwareShaderProgram | None, interpolated: dict[str, float]) -> tuple[int, int, int, int]:
        if fragment_shader is None:
            return (255, 255, 255, 255)
        return fragment_shader.emulate_fragment_shader(interpolated)

    def clear(self, color: tuple[int, int, int, int] | None = None) -> None:
        """Clear the framebuffer and depth buffer.

        Args:
            color: Clear color (r, g, b, a). If None, uses current clear color.
        """
        with self._lock:
            if color is None:
                color = self._clear_color

            for y in range(self._height):
                for x in range(self._width):
                    self._framebuffer[y][x] = color
                    self._depth_buffer[y][x] = float("inf")

    def set_clear_color(self, color: tuple[int, int, int, int]) -> None:
        """Set the clear color.

        Args:
            color: Clear color (r, g, b, a).
        """
        self._clear_color = color

    def get_framebuffer(self) -> list[list[tuple[int, int, int, int]]]:
        """Get the current framebuffer contents.

        Returns:
            Copy of the framebuffer.
        """
        with self._lock:
            return [row[:] for row in self._framebuffer]

    def resize(self, width: int, height: int) -> None:
        """Resize the framebuffer.

        Args:
            width: New width.
            height: New height.
        """
        with self._lock:
            self._width = width
            self._height = height
            self._initialize_buffers()

    def _reset_depth_buffer(self) -> None:
        for row in self._depth_buffer:
            for index in range(len(row)):
                row[index] = float("inf")

    def _sync_viewport(self, pipeline: SoftwarePipeline) -> None:
        if (
            self._width != pipeline.config.viewport_width
            or self._height != pipeline.config.viewport_height
        ):
            self.resize(pipeline.config.viewport_width, pipeline.config.viewport_height)

    @staticmethod
    def _resolve_vertex_shader(pipeline: SoftwarePipeline, shader: Shader) -> SoftwareShaderProgram | None:
        vertex_program = pipeline.get_vertex_shader()
        if vertex_program is not None:
            return vertex_program
        if isinstance(shader.program, dict):
            return shader.program.get("software_program")
        if hasattr(shader.program, "emulate_vertex_shader"):
            return shader.program
        return None

    @staticmethod
    def _resolve_fragment_shader(pipeline: SoftwarePipeline, shader: Shader) -> SoftwareShaderProgram | None:
        fragment_program = pipeline.get_fragment_shader()
        if fragment_program is not None:
            return fragment_program
        if isinstance(shader.program, dict):
            return shader.program.get("software_program")
        if hasattr(shader.program, "emulate_fragment_shader"):
            return shader.program
        return None