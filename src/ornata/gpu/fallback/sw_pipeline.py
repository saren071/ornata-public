# Software pipeline state management for GPU fallback implementation.
"""Software pipeline state management for GPU fallback implementation."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import BlendFactor, BlendOperation, DepthFunction, PipelineConfig
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.gpu.fallback.math import Matrix4
    from ornata.gpu.fallback.sw_textures import SwTexture2D

logger = get_logger(__name__)


class SoftwareShaderProgram:
    """Emulation of shader program for software pipeline."""

    def __init__(self, vertex_source: str, fragment_source: str) -> None:
        """Initialize software shader program emulation.

        Args:
            vertex_source: Vertex shader source code.
            fragment_source: Fragment shader source code.
        """
        self.vertex_source = vertex_source
        self.fragment_source = fragment_source
        self._uniforms: dict[str, Any] = {}
        self._attributes: dict[str, Any] = {}
        self._textures: dict[int, SwTexture2D] = {}

    def set_uniform(self, name: str, value: Any) -> None:
        """Set uniform value for shader emulation.

        Args:
            name: Uniform variable name.
            value: Uniform value.
        """
        self._uniforms[name] = value

    def get_uniform(self, name: str) -> Any:
        """Get uniform value.

        Args:
            name: Uniform variable name.

        Returns:
            Uniform value.
        """
        return self._uniforms.get(name)

    def bind_texture(self, slot: int, texture: SwTexture2D) -> None:
        """Bind a software texture to a sampler slot."""
        self._textures[int(slot)] = texture

    def unbind_texture(self, slot: int) -> None:
        """Unbind a texture from the specified slot."""
        self._textures.pop(int(slot), None)

    def get_texture(self, slot: int) -> SwTexture2D | None:
        """Retrieve bound texture for the slot, if any."""
        return self._textures.get(int(slot))

    def clear_textures(self) -> None:
        """Remove all bound textures."""
        self._textures.clear()

    def set_attribute(self, name: str, value: Any) -> None:
        """Set attribute value for shader emulation.

        Args:
            name: Attribute variable name.
            value: Attribute value.
        """
        self._attributes[name] = value

    def get_attribute(self, name: str) -> Any:
        """Get attribute value.

        Args:
            name: Attribute variable name.

        Returns:
            Attribute value.
        """
        return self._attributes.get(name)

    def emulate_vertex_shader(self, vertex_data: list[float]) -> list[float]:
        """Emulate vertex shader processing.

        Args:
            vertex_data: Input vertex data.

        Returns:
            Transformed vertex data.
        """
        transform = self.get_uniform("u_transform")
        if transform is None:
            return vertex_data

        matrix = coerce_matrix(transform)
        x, y, z, u_coord, v_coord = vertex_data[:5]
        from ornata.gpu.fallback.math import transform_point
        tx, ty, tz = transform_point(matrix, (x, y, z))
        return [tx, ty, tz, u_coord, v_coord]

    def emulate_fragment_shader(self, interpolated_data: dict[str, float]) -> tuple[int, int, int, int]:
        """Emulate fragment shader processing.

        Args:
            interpolated_data: Interpolated vertex data.

        Returns:
            RGBA color tuple.
        """
        color_uniform = self.get_uniform("u_color")
        if isinstance(color_uniform, (list, tuple)) and len(color_uniform) == 4:
            r_component = int(max(0.0, min(1.0, float(color_uniform[0]))) * 255)
            g_component = int(max(0.0, min(1.0, float(color_uniform[1]))) * 255)
            b_component = int(max(0.0, min(1.0, float(color_uniform[2]))) * 255)
            a_component = int(max(0.0, min(1.0, float(color_uniform[3]))) * 255)
            base_color = (r_component, g_component, b_component, a_component)
        else:
            base_color = (255, 255, 255, 255)

        texture_slot = int(self.get_uniform("u_texture_slot") or 0)
        texture = self.get_texture(texture_slot)
        if texture is not None:
            u_coord = interpolated_data.get("tex_u", 0.0)
            v_coord = interpolated_data.get("tex_v", 0.0)
            sampled = texture.sample_bilinear(u_coord, v_coord)
            sampled_color = (
                int(sampled[0]),
                int(sampled[1]),
                int(sampled[2]),
                int(sampled[3]),
            )
            return (
                int(sampled_color[0] * base_color[0] / 255),
                int(sampled_color[1] * base_color[1] / 255),
                int(sampled_color[2] * base_color[2] / 255),
                int(sampled_color[3] * base_color[3] / 255),
            )

        return base_color


class SoftwarePipeline:
    """Software pipeline state manager for GPU fallback."""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        """Initialize software pipeline.

        Args:
            config: Pipeline configuration. Uses defaults if None.
        """
        self.config = config or PipelineConfig()
        self._vertex_shader: SoftwareShaderProgram | None = None
        self._fragment_shader: SoftwareShaderProgram | None = None
        self._bound = False

    def set_config(self, config: PipelineConfig) -> None:
        """Update pipeline configuration.

        Args:
            config: New pipeline configuration.
        """
        self.config = config
        logger.debug("Updated software pipeline configuration")

    def set_vertex_shader(self, shader: SoftwareShaderProgram) -> None:
        """Set vertex shader program.

        Args:
            shader: Vertex shader program.
        """
        self._vertex_shader = shader

    def set_fragment_shader(self, shader: SoftwareShaderProgram) -> None:
        """Set fragment shader program.

        Args:
            shader: Fragment shader program.
        """
        self._fragment_shader = shader

    def bind(self) -> None:
        """Bind the pipeline for rendering."""
        if not self._vertex_shader or not self._fragment_shader:
            raise ValueError("Both vertex and fragment shaders must be set before binding")

        self._bound = True
        logger.debug("Bound software pipeline for rendering")

    def unbind(self) -> None:
        """Unbind the pipeline."""
        self._bound = False

    def is_bound(self) -> bool:
        """Check if pipeline is currently bound.

        Returns:
            True if bound, False otherwise.
        """
        return self._bound

    def apply_blend_state(self, src_color: tuple[int, int, int, int], dst_color: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        """Apply blending operation to colors.

        Args:
            src_color: Source color (r, g, b, a).
            dst_color: Destination color (r, g, b, a).

        Returns:
            Blended color (r, g, b, a).
        """
        if not self.config.blend_state.enabled:
            return src_color

        src_rgb_factor = resolve_blend_factor(self.config.blend_state.src_factor, src_color, dst_color)
        dst_rgb_factor = resolve_blend_factor(self.config.blend_state.dst_factor, src_color, dst_color)

        blended_rgb: list[int] = []
        for index in range(3):
            blended_component = self._apply_operation(
                self.config.blend_state.operation,
                src_color[index] * src_rgb_factor[index],
                dst_color[index] * dst_rgb_factor[index],
            )
            blended_rgb.append(int(max(0.0, min(255.0, blended_component))))

        src_alpha_factor = resolve_blend_factor(self.config.blend_state.src_alpha_factor, src_color, dst_color)
        dst_alpha_factor = resolve_blend_factor(self.config.blend_state.dst_alpha_factor, src_color, dst_color)
        blended_alpha = self._apply_operation(
            self.config.blend_state.alpha_operation,
            src_color[3] * src_alpha_factor[3],
            dst_color[3] * dst_alpha_factor[3],
        )

        alpha_int = int(max(0.0, min(255.0, blended_alpha)))
        return (blended_rgb[0], blended_rgb[1], blended_rgb[2], alpha_int)

    def apply_depth_test(self, current_depth: float, buffer_depth: float) -> bool:
        """Apply depth testing.

        Args:
            current_depth: Current fragment depth.
            buffer_depth: Depth buffer value.

        Returns:
            True if fragment passes depth test.
        """
        if not self.config.depth_state.enabled:
            return True

        func = self.config.depth_state.function
        if func == DepthFunction.LESS:
            return current_depth < buffer_depth
        elif func == DepthFunction.LESS_EQUAL:
            return current_depth <= buffer_depth
        elif func == DepthFunction.GREATER:
            return current_depth > buffer_depth
        elif func == DepthFunction.GREATER_EQUAL:
            return current_depth >= buffer_depth
        elif func == DepthFunction.EQUAL:
            return current_depth == buffer_depth
        elif func == DepthFunction.NOT_EQUAL:
            return current_depth != buffer_depth
        elif func == DepthFunction.ALWAYS:
            return True
        elif func == DepthFunction.NEVER:
            return False

        return True

    def get_vertex_shader(self) -> SoftwareShaderProgram | None:
        """Get current vertex shader.

        Returns:
            Vertex shader program or None.
        """
        return self._vertex_shader

    def get_fragment_shader(self) -> SoftwareShaderProgram | None:
        """Get current fragment shader.

        Returns:
            Fragment shader program or None.
        """
        return self._fragment_shader

    @staticmethod
    def _apply_operation(operation: BlendOperation, src: float, dst: float) -> float:
        if operation == BlendOperation.ADD:
            return src + dst
        if operation == BlendOperation.SUBTRACT:
            return src - dst
        if operation == BlendOperation.REVERSE_SUBTRACT:
            return dst - src
        if operation == BlendOperation.MIN:
            return min(src, dst)
        if operation == BlendOperation.MAX:
            return max(src, dst)
        return src


def coerce_matrix(raw: Any) -> Matrix4:
    from ornata.gpu.fallback.math import Matrix4
    if isinstance(raw, Matrix4):
        return raw
    if isinstance(raw, (list, tuple)) and len(raw) == 16:
        rows = [list(map(float, raw[index:index + 4])) for index in range(0, 16, 4)]
        return Matrix4(rows)
    raise ValueError("Uniform u_transform must be a Matrix4 or flat iterable with 16 elements")


def resolve_blend_factor(factor: BlendFactor, src: tuple[int, int, int, int], dst: tuple[int, int, int, int]) -> tuple[float, float, float, float]:
    src_rgb = tuple(component / 255.0 for component in src[:3])
    dst_rgb = tuple(component / 255.0 for component in dst[:3])
    src_alpha = src[3] / 255.0
    dst_alpha = dst[3] / 255.0

    if factor == BlendFactor.ZERO:
        return (0.0, 0.0, 0.0, 0.0)
    if factor == BlendFactor.ONE:
        return (1.0, 1.0, 1.0, 1.0)
    if factor == BlendFactor.SRC_COLOR:
        return (src_rgb[0], src_rgb[1], src_rgb[2], src_alpha)
    if factor == BlendFactor.ONE_MINUS_SRC_COLOR:
        return (1.0 - src_rgb[0], 1.0 - src_rgb[1], 1.0 - src_rgb[2], 1.0 - src_alpha)
    if factor == BlendFactor.DST_COLOR:
        return (dst_rgb[0], dst_rgb[1], dst_rgb[2], dst_alpha)
    if factor == BlendFactor.ONE_MINUS_DST_COLOR:
        return (1.0 - dst_rgb[0], 1.0 - dst_rgb[1], 1.0 - dst_rgb[2], 1.0 - dst_alpha)
    if factor == BlendFactor.SRC_ALPHA:
        return (src_alpha, src_alpha, src_alpha, src_alpha)
    if factor == BlendFactor.ONE_MINUS_SRC_ALPHA:
        inv = 1.0 - src_alpha
        return (inv, inv, inv, inv)
    if factor == BlendFactor.DST_ALPHA:
        return (dst_alpha, dst_alpha, dst_alpha, dst_alpha)
    if factor == BlendFactor.ONE_MINUS_DST_ALPHA:
        inv = 1.0 - dst_alpha
        return (inv, inv, inv, inv)
    return (1.0, 1.0, 1.0, 1.0)