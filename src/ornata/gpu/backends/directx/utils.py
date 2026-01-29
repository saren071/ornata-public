# ===========================
# ornata/gpu/backends/directx/utils.py  (utilities used across the DirectX backend)
# ===========================
"""DirectX utility functions and constants module.

This module provides math/layout helpers used by the DirectX backend — notably,
conversion from pixel coordinates to Normalized Device Coordinates (NDC) in
DirectX's clip space convention, and a few defaults used by the backend.
"""

from __future__ import annotations

from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


def to_ndc_vertices(vertices: list[float], width: int, height: int) -> list[float]:
    """Convert pixel-space vertices to clip-space (NDC) for DirectX.

    The input is interleaved floats with a stride of 5:

        [x, y, z, u, v,  x, y, z, u, v,  ...]

    where `x, y` are in pixel coordinates for a viewport of (width, height).
    Output preserves the same interleaving with x/y converted to NDC:

        x_ndc = (x / (width * 0.5)) - 1.0
        y_ndc = 1.0 - (y / (height * 0.5))

    Args:
        vertices: Interleaved [x, y, z, u, v, ...] in pixels.
        width: Viewport width in pixels.
        height: Viewport height in pixels.

    Returns:
        Interleaved floats with x/y converted to NDC.
    """
    if width <= 0 or height <= 0:
        raise ValueError("width/height must be positive")
    if len(vertices) % 5 != 0:
        raise ValueError("vertices must be a multiple of 5 (x, y, z, u, v)")

    ndc: list[float] = []
    for i in range(0, len(vertices), 5):
        x = float(vertices[i + 0])
        y = float(vertices[i + 1])
        z = float(vertices[i + 2])
        u = float(vertices[i + 3])
        v = float(vertices[i + 4])

        ndc_x = (x / (width * 0.5)) - 1.0
        ndc_y = 1.0 - (y / (height * 0.5))
        ndc.extend([ndc_x, ndc_y, z, u, v])
    return ndc


def get_default_viewport() -> dict[str, float]:
    """Return default viewport parameters used by the backend."""
    return {
        "top_left_x": 0.0,
        "top_left_y": 0.0,
        "width": 800.0,
        "height": 600.0,
        "min_depth": 0.0,
        "max_depth": 1.0,
    }


def get_clear_color() -> tuple[float, float, float, float]:
    """Return default clear color RGBA."""
    return (0.0, 0.0, 0.0, 1.0)


def get_vertex_stride() -> int:
    """Return the vertex stride (5 floats * 4 bytes)."""
    return 5 * 4


def get_instance_stride() -> int:
    """Return the instance stride (5 floats * 4 bytes)."""
    return 5 * 4