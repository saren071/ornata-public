"""Auto-generated exports for ornata.gpu.fallback."""

from __future__ import annotations

from . import batching, blitter, cpu_fallback, instancing, math, rasterizer, sw_buffers, sw_pipeline, sw_textures
from .batching import CPUFallbackBatcher, GeometryBatch
from .blitter import CPUBlitter
from .cpu_fallback import CPUFallback
from .instancing import CPUInstancer
from .math import (
    identity_matrix,
    look_at_matrix,
    matrix_multiply,
    ndc_to_screen,
    orthographic_matrix,
    perspective_matrix,
    rotate_x_matrix,
    rotate_y_matrix,
    rotate_z_matrix,
    scale_matrix,
    screen_to_ndc,
    transform_point,
    transform_vector,
    translate_matrix,
    vector_add,
    vector_cross,
    vector_dot,
    vector_length,
    vector_normalize,
    vector_scale,
    vector_subtract,
    viewport_matrix,
)
from .rasterizer import SoftwareRasterizer
from .sw_buffers import SwIndexBuffer, SwVertexBuffer
from .sw_pipeline import SoftwarePipeline, SoftwareShaderProgram, coerce_matrix, resolve_blend_factor
from .sw_textures import SwTexture2D, process_texture_coordinates

__all__ = [
    "CPUBlitter",
    "CPUFallback",
    "CPUFallbackBatcher",
    "CPUInstancer",
    "GeometryBatch",
    "SoftwarePipeline",
    "SoftwareRasterizer",
    "SoftwareShaderProgram",
    "SwIndexBuffer",
    "SwTexture2D",
    "SwVertexBuffer",
    "coerce_matrix",
    "resolve_blend_factor",
    "batching",
    "blitter",
    "cpu_fallback",
    "identity_matrix",
    "instancing",
    "look_at_matrix",
    "math",
    "matrix_multiply",
    "ndc_to_screen",
    "orthographic_matrix",
    "perspective_matrix",
    "process_texture_coordinates",
    "rasterizer",
    "rotate_x_matrix",
    "rotate_y_matrix",
    "rotate_z_matrix",
    "scale_matrix",
    "screen_to_ndc",
    "sw_buffers",
    "sw_pipeline",
    "sw_textures",
    "transform_point",
    "transform_vector",
    "translate_matrix",
    "vector_add",
    "vector_cross",
    "vector_dot",
    "vector_length",
    "vector_normalize",
    "vector_scale",
    "vector_subtract",
    "viewport_matrix",
]
