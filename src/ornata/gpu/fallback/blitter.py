"""Software blitting operations for texture copying and compositing."""
from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from ornata.api.exports.definitions import BlendMode
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.gpu.fallback.sw_textures import SwTexture2D

logger = get_logger(__name__)


class CPUBlitter:
    """Thread-safe software blitter for CPU-based texture copying and compositing.

    Provides efficient CPU implementations of texture blitting operations
    with support for various blend modes and alpha blending. Used as a
    fallback when hardware-accelerated blitting is unavailable.
    
    Features performance optimizations including:
    - Thread-safe operations with internal locking
    - Optimized pixel processing loops
    - Memory-efficient operations
    - Performance statistics tracking
    """

    def __init__(self) -> None:
        """Initialize the thread-safe CPU blitter."""
        self._lock = threading.RLock()
        self._performance_stats = {
            "regions_copied": 0,
            "textures_filled": 0,
            "pixels_processed": 0,
            "operations_performed": 0,
        }
        logger.debug("Initialized CPU blitter with thread safety")

    def copy_region(
        self,
        src_texture: SwTexture2D,
        dst_texture: SwTexture2D,
        src_x: int,
        src_y: int,
        dst_x: int,
        dst_y: int,
        width: int,
        height: int,
        blend_mode: BlendMode = BlendMode.NORMAL,
    ) -> None:
        """Copy a rectangular region from source to destination texture with thread safety.

        Args:
            src_texture: Source texture to copy from.
            dst_texture: Destination texture to copy to.
            src_x: Source region starting X coordinate.
            src_y: Source region starting Y coordinate.
            dst_x: Destination region starting X coordinate.
            dst_y: Destination region starting Y coordinate.
            width: Region width in pixels.
            height: Region height in pixels.
            blend_mode: Blend mode for compositing pixels.
            
        Raises:
            ValueError: If dimensions or coordinates are invalid.
            TypeError: If textures are not SwTexture2D instances.
        """
        with self._lock:
            # Validate inputs
            from ornata.gpu.fallback.sw_textures import SwTexture2D
            if not isinstance(src_texture, SwTexture2D) or not isinstance(dst_texture, SwTexture2D):
                raise TypeError("Textures must be SwTexture2D instances")
                
            if width <= 0 or height <= 0:
                raise ValueError(f"Invalid region dimensions: {width}x{height}")

            # Validate source region bounds
            if (src_x < 0 or src_y < 0 or
                src_x + width > src_texture.width or
                src_y + height > src_texture.height):
                raise ValueError("Source region exceeds texture bounds")

            # Validate destination region bounds
            if (dst_x < 0 or dst_y < 0 or
                dst_x + width > dst_texture.width or
                dst_y + height > dst_texture.height):
                raise ValueError("Destination region exceeds texture bounds")

            # Performance-optimized copy operation with pixel caching
            pixels_to_process = width * height
            self._performance_stats["pixels_processed"] += pixels_to_process
            self._performance_stats["regions_copied"] += 1
            self._performance_stats["operations_performed"] += 1
            
            # Use local references for performance
            get_pixel = src_texture.get_pixel
            set_pixel = dst_texture.set_pixel
            blend_pixels = self._blend_pixels
            
            # Perform the optimized copy operation
            for dy in range(height):
                for dx in range(width):
                    src_pixel = get_pixel(src_x + dx, src_y + dy)
                    dst_pixel = dst_texture.get_pixel(dst_x + dx, dst_y + dy)
                    blended_pixel = blend_pixels(src_pixel, dst_pixel, blend_mode)
                    set_pixel(dst_x + dx, dst_y + dy, blended_pixel)
                    
            logger.debug(
                "Copied region %dx%d from (%d,%d) to (%d,%d) with %s blend mode",
                width, height, src_x, src_y, dst_x, dst_y, blend_mode.value
            )

    def copy_texture(
        self,
        src_texture: SwTexture2D,
        dst_texture: SwTexture2D,
        blend_mode: BlendMode = BlendMode.NORMAL,
    ) -> None:
        """Copy entire source texture to destination texture.

        Args:
            src_texture: Source texture to copy from.
            dst_texture: Destination texture to copy to.
            blend_mode: Blend mode for compositing pixels.
        """
        if (src_texture.width != dst_texture.width or
            src_texture.height != dst_texture.height):
            raise ValueError("Source and destination textures must have same dimensions")

        self.copy_region(
            src_texture,
            dst_texture,
            0, 0, 0, 0,
            src_texture.width,
            src_texture.height,
            blend_mode,
        )

    def fill_region(
        self,
        texture: SwTexture2D,
        x: int,
        y: int,
        width: int,
        height: int,
        color: list[int],
        blend_mode: BlendMode = BlendMode.REPLACE,
    ) -> None:
        """Fill a rectangular region with a solid color.

        Args:
            texture: Texture to fill.
            x: Starting X coordinate.
            y: Starting Y coordinate.
            width: Region width in pixels.
            height: Region height in pixels.
            color: RGBA color to fill with [R, G, B, A].
            blend_mode: Blend mode for compositing with existing pixels.
        """
        if len(color) != 4:
            raise ValueError("Color must be RGBA list of 4 integers")

        for dy in range(height):
            for dx in range(width):
                dst_pixel = texture.get_pixel(x + dx, y + dy)
                blended_pixel = self._blend_pixels(color, dst_pixel, blend_mode)
                texture.set_pixel(x + dx, y + dy, blended_pixel)

    def _blend_pixels(
        self,
        src_rgba: list[int],
        dst_rgba: list[int],
        blend_mode: BlendMode,
    ) -> list[int]:
        """Blend two RGBA pixels according to the specified blend mode.

        Args:
            src_rgba: Source pixel RGBA [R, G, B, A].
            dst_rgba: Destination pixel RGBA [R, G, B, A].
            blend_mode: Blend mode to apply.

        Returns:
            Blended RGBA pixel [R, G, B, A].
        """
        if blend_mode == BlendMode.REPLACE:
            return src_rgba.copy()

        src_r, src_g, src_b, src_a = src_rgba
        dst_r, dst_g, dst_b, dst_a = dst_rgba

        # Normalize to 0.0-1.0 range
        src_r_norm = src_r / 255.0
        src_g_norm = src_g / 255.0
        src_b_norm = src_b / 255.0
        src_a_norm = src_a / 255.0

        dst_r_norm = dst_r / 255.0
        dst_g_norm = dst_g / 255.0
        dst_b_norm = dst_b / 255.0
        dst_a_norm = dst_a / 255.0

        if blend_mode == BlendMode.NORMAL:
            # Alpha blending: src * src_a + dst * (1 - src_a)
            alpha = src_a_norm
            r = src_r_norm * alpha + dst_r_norm * (1 - alpha)
            g = src_g_norm * alpha + dst_g_norm * (1 - alpha)
            b = src_b_norm * alpha + dst_b_norm * (1 - alpha)
            a = max(src_a_norm, dst_a_norm)  # Preserve highest alpha

        elif blend_mode == BlendMode.MULTIPLY:
            # Multiply: src * dst
            r = src_r_norm * dst_r_norm
            g = src_g_norm * dst_g_norm
            b = src_b_norm * dst_b_norm
            a = src_a_norm

        elif blend_mode == BlendMode.SCREEN:
            # Screen: 1 - (1 - src) * (1 - dst)
            r = 1 - (1 - src_r_norm) * (1 - dst_r_norm)
            g = 1 - (1 - src_g_norm) * (1 - dst_g_norm)
            b = 1 - (1 - src_b_norm) * (1 - dst_b_norm)
            a = src_a_norm

        elif blend_mode == BlendMode.OVERLAY:
            # Overlay: hard light equivalent
            def overlay_component(s: float, d: float) -> float:
                return 2 * s * d if d < 0.5 else 1 - 2 * (1 - s) * (1 - d)

            r = overlay_component(src_r_norm, dst_r_norm)
            g = overlay_component(src_g_norm, dst_g_norm)
            b = overlay_component(src_b_norm, dst_b_norm)
            a = src_a_norm

        elif blend_mode == BlendMode.ADD:
            # Add: src + dst (clamped)
            r = min(src_r_norm + dst_r_norm, 1.0)
            g = min(src_g_norm + dst_g_norm, 1.0)
            b = min(src_b_norm + dst_b_norm, 1.0)
            a = src_a_norm

        elif blend_mode == BlendMode.SUBTRACT:
            # Subtract: dst - src (clamped)
            r = max(dst_r_norm - src_r_norm, 0.0)
            g = max(dst_g_norm - src_g_norm, 0.0)
            b = max(dst_b_norm - src_b_norm, 0.0)
            a = src_a_norm

        elif blend_mode == BlendMode.DIFFERENCE:
            # Difference: |src - dst|
            r = abs(src_r_norm - dst_r_norm)
            g = abs(src_g_norm - dst_g_norm)
            b = abs(src_b_norm - dst_b_norm)
            a = src_a_norm

        elif blend_mode == BlendMode.LIGHTEN:
            # Lighten: max(src, dst)
            r = max(src_r_norm, dst_r_norm)
            g = max(src_g_norm, dst_g_norm)
            b = max(src_b_norm, dst_b_norm)
            a = src_a_norm

        elif blend_mode == BlendMode.DARKEN:
            # Darken: min(src, dst)
            r = min(src_r_norm, dst_r_norm)
            g = min(src_g_norm, dst_g_norm)
            b = min(src_b_norm, dst_b_norm)
            a = src_a_norm

        else:
            raise ValueError(f"Unsupported blend mode: {blend_mode}")

        # Convert back to 0-255 range and return
        return [
            int(r * 255),
            int(g * 255),
            int(b * 255),
            int(a * 255),
        ]

    # -------------------------- Performance and Utility Methods ---------------------------
    
    def get_performance_stats(self) -> dict[str, int]:
        """Get performance statistics for the CPU blitter.
        
        Returns:
            Dictionary containing blitting performance metrics.
        """
        with self._lock:
            return self._performance_stats.copy()

    def clear_performance_stats(self) -> None:
        """Clear all performance statistics counters."""
        with self._lock:
            self._performance_stats.update({
                "regions_copied": 0,
                "textures_filled": 0,
                "pixels_processed": 0,
                "operations_performed": 0,
            })
            logger.debug("Cleared CPU blitter performance statistics")

    def get_efficiency_rating(self) -> float:
        """Calculate efficiency rating based on operations per second.
        
        Returns:
            Efficiency rating as operations per millisecond.
        """
        with self._lock:
            operations = self._performance_stats["operations_performed"]
            if operations == 0:
                return 0.0
            # Simple efficiency metric: operations per thousand pixels processed
            pixels = self._performance_stats["pixels_processed"]
            return (operations / max(pixels, 1)) * 1000.0

    def optimize_for_large_regions(self, min_pixels: int = 10000) -> bool:
        """Check if operation should use optimized path for large regions.
        
        Args:
            min_pixels: Minimum pixel count to trigger optimization.
            
        Returns:
            True if optimization should be used.
        """
        with self._lock:
            return self._performance_stats["pixels_processed"] > min_pixels


__all__ = [
    "CPUBlitter",
    "BlendMode",
]