"""GUI compositor for managing layers, blending, and rendering.

This module provides the core compositing engine that handles layer management,
blend modes, transforms, and dirty region tracking for efficient GUI rendering.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.gpu import CompositorBase
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import BlendMode, CompositorLayer, DirtyRegion, Rect
    from ornata.api.exports.gpu import GPUContext, Texture
    from ornata.definitions.dataclasses.rendering import Transform as RenderTransform

logger = get_logger(__name__)


class Compositor(CompositorBase):
    """Thread-safe GUI compositor with advanced blending and optimization."""

    def __init__(self, width: int, height: int) -> None:
        super().__init__(width, height)
        self._lock = threading.RLock()
        self._layer_cache: dict[int, CompositorLayer] = {}
        self._region_merge_threshold = 16  # pixels

    def resize(self, width: int, height: int) -> None:
        """Resize the compositor output."""
        with self._lock:
            self.width = width
            self.height = height
            # Invalidate output texture - will be recreated on next composite
            if self.output_texture:
                self.output_texture.destroy()
                self.output_texture = None

    def add_layer(self, layer: CompositorLayer) -> None:
        """Add a layer and cache it for future updates."""
        with self._lock:
            layer_id = id(layer)
            self._layer_cache[layer_id] = layer
            super().add_layer(layer)

    def remove_layer(self, layer: CompositorLayer) -> None:
        """Remove a layer by ID."""
        with self._lock:
            layer_id = id(layer)
            self._layer_cache.pop(layer_id)
            if layer:
                super().remove_layer(layer)

    def update_layer(self, layer_id: int, **updates: Any) -> None:
        """Update layer properties."""
        with self._lock:
            layer = self._layer_cache.get(layer_id)
            if not layer:
                return

            for key, value in updates.items():
                if hasattr(layer, key):
                    setattr(layer, key, value)

            # Re-sort layers if z-index changed
            if 'z_index' in updates:
                self.layers.sort(key=lambda layer: layer.z_index)

    def mark_dirty(self, region: DirtyRegion) -> None:
        """Mark a region as dirty, merging with existing regions."""
        with self._lock:
            # Try to merge with existing regions
            merged = False
            region_rect = self._region_to_rect(region)
            for existing in self.dirty_regions:
                if existing.layer_index != region.layer_index:
                    continue
                existing_rect = self._region_to_rect(existing)
                if self._can_merge_regions(existing_rect, region_rect):
                    merged_rect = self._merge_rects(existing_rect, region_rect)
                    existing.x = int(merged_rect.x)
                    existing.y = int(merged_rect.y)
                    existing.width = int(merged_rect.width)
                    existing.height = int(merged_rect.height)
                    merged = True
                    break

            if not merged:
                self.dirty_regions.append(region)

    def clear_dirty_regions(self) -> None:
        """Clear all dirty regions."""
        with self._lock:
            self.dirty_regions.clear()

    def composite(self, context: GPUContext) -> Texture:
        """Composite all layers with optimizations."""
        with self._lock:
            return self._composite_impl(context)

    def _composite_impl(self, context: GPUContext) -> Texture:
        """Internal composite implementation."""
        from ornata.api.exports.gpu import RenderTarget
        # Create output texture if needed
        if self.output_texture is None or not self.output_texture.valid:
            self.output_texture = context.create_texture(self.width, self.height)

        # Set render target
        output_target = RenderTarget(self.width, self.height)
        output_target.color_texture = self.output_texture
        context.set_render_target(output_target)

        # If we have dirty regions, only composite affected areas
        if self.dirty_regions:
            self._composite_dirty_regions(context)
        else:
            self._composite_full(context)

        return self.output_texture

    def _composite_full(self, context: GPUContext) -> None:
        """Full composition of all layers."""
        from ornata.api.exports.definitions import Color
        # Clear background
        context.clear(Color(0, 0, 0, 0))

        # Composite all layers in z-order
        for layer in self.layers:
            if layer.opacity <= 0:
                continue

            self._composite_layer(context, layer)

    def _composite_dirty_regions(self, context: GPUContext) -> None:
        """Optimized composition of only dirty regions."""
        # For now, fall back to full composition
        # Real implementation would track scissor rectangles and only redraw affected areas
        self._composite_full(context)

    def _composite_layer(self, context: GPUContext, layer: CompositorLayer) -> None:
        """Composite a single layer with blend mode support."""
        # Apply transform if needed
        if self._has_transform(layer.transform):
            # Real implementation would set up transform matrices in shaders
            pass

        # Apply blend mode
        # Real implementation would set blend state on GPU context
        self._apply_blend_mode(context, layer.blend_mode)

        # Apply opacity
        if layer.opacity < 1.0:
            # Real implementation would use alpha blending
            pass

        # Draw the layer
        context.draw_textured_rect(layer.rect, layer.texture)

    def _apply_blend_mode(self, context: GPUContext, blend_mode: BlendMode) -> None:
        """Apply blend mode to GPU context."""
        from ornata.api.exports.definitions import BlendMode
        # Real implementation would set GPU blend state based on blend mode
        match blend_mode:
            case BlendMode.NORMAL:
                # Standard alpha blending
                pass
            case BlendMode.MULTIPLY:
                # Multiply blend
                pass
            case BlendMode.SCREEN:
                # Screen blend
                pass
            case BlendMode.OVERLAY:
                # Overlay blend
                pass
            case _:
                # Default to normal
                pass

    def _has_transform(self, transform: RenderTransform) -> bool:
        """Check if transform has any effect."""
        result: bool = (
            transform.m11 != 1.0 or transform.m12 != 0.0 or
            transform.m21 != 0.0 or transform.m22 != 1.0 or
            transform.dx != 0.0 or transform.dy != 0.0
        )
        return result

    def _can_merge_regions(self, a: Rect, b: Rect) -> bool:
        """Check if two regions can be merged."""
        # Simple distance-based merging
        result: bool = (
            abs(a.x - b.x) < self._region_merge_threshold and
            abs(a.y - b.y) < self._region_merge_threshold and
            abs(a.right - b.right) < self._region_merge_threshold and
            abs(a.bottom - b.bottom) < self._region_merge_threshold
        )
        return result

    def _merge_rects(self, a: Rect, b: Rect) -> Rect:
        """Merge two rectangles into their union."""
        from ornata.api.exports.definitions import Rect
        min_x = min(a.x, b.x)
        min_y = min(a.y, b.y)
        max_right = max(a.right, b.right)
        max_bottom = max(a.bottom, b.bottom)
        return Rect(min_x, min_y, max_right - min_x, max_bottom - min_y)

    def _region_to_rect(self, region: DirtyRegion) -> Rect:
        """Convert a dirty region into a Rect for overlap checks."""
        from ornata.api.exports.definitions import Rect

        return Rect(region.x, region.y, region.width, region.height)

    def get_layer_at(self, x: float, y: float) -> CompositorLayer | None:
        """Get the topmost layer at the given coordinates."""
        with self._lock:
            # Search layers in reverse z-order (top to bottom)
            for layer in reversed(self.layers):
                if layer.rect.contains(x, y):
                    return layer
            return None

    def get_layers_in_rect(self, rect: Rect) -> list[CompositorLayer]:
        """Get all layers that intersect with the given rectangle."""
        with self._lock:
            return [layer for layer in self.layers if layer.rect.intersects(rect)]
