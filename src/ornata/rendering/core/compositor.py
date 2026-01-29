"""Layer composition system for combining multiple surfaces.

The compositor handles blending multiple rendering layers together
into a final output surface, supporting various blend modes and transforms.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Layer, PixelSurface, Surface

logger = get_logger(__name__)


class Compositor:
    """Manages composition of multiple rendering layers.
    
    The compositor combines layers according to their z-index, blend modes,
    and transforms to produce a final composite surface.
    
    Parameters
    ----------
    width : int
        Target composition width in renderer units.
    height : int
        Target composition height in renderer units.
        
    Returns
    -------
    Compositor
        A layer compositor instance.
    """

    def __init__(self, width: int, height: int) -> None:
        """Initialize the compositor.

        Parameters
        ----------
        width : int
            Target composition width.
        height : int
            Target composition height.

        Returns
        -------
        None
        """
        self.width = width
        self.height = height
        self._layers: dict[str, Layer] = {}
        self._dirty_regions: list[tuple[int, int, int, int]] = []  # (x, y, width, height)
        self._last_composition: Surface | None = None
        logger.debug(f"Initialized Compositor ({width}x{height})")

    def add_layer(self, layer: Layer) -> None:
        """Add a layer to the composition.

        Parameters
        ----------
        layer : Layer
            The layer to add.

        Returns
        -------
        None
        """
        if layer.name in self._layers:
            logger.warning(f"Replacing existing layer: {layer.name}")
        self._layers[layer.name] = layer

        # Mark the entire layer area as dirty
        if layer.surface:
            self._mark_dirty_region(0, 0, layer.surface.width, layer.surface.height)

        logger.log(5, f"Added layer '{layer.name}' (z={layer.z_index})")

    def remove_layer(self, name: str) -> None:
        """Remove a layer from the composition.

        Parameters
        ----------
        name : str
            Name of the layer to remove.

        Returns
        -------
        None
        """
        if name in self._layers:
            layer = self._layers[name]
            del self._layers[name]

            # Mark the layer area as dirty
            if layer.surface:
                self._mark_dirty_region(0, 0, layer.surface.width, layer.surface.height)

            logger.log(5, f"Removed layer '{name}'")
        else:
            logger.warning(f"Attempted to remove non-existent layer: {name}")

    def get_layer(self, name: str) -> Layer | None:
        """Get a layer by name.
        
        Parameters
        ----------
        name : str
            Name of the layer to retrieve.
            
        Returns
        -------
        Layer | None
            The layer if found, None otherwise.
        """
        return self._layers.get(name)

    def set_layer_visibility(self, name: str, visible: bool) -> None:
        """Set the visibility of a layer.
        
        Parameters
        ----------
        name : str
            Name of the layer.
        visible : bool
            New visibility state.
            
        Returns
        -------
        None
        """
        layer = self._layers.get(name)
        if layer:
            layer.visible = visible
            logger.log(5, f"Layer '{name}' visibility set to {visible}")
        else:
            logger.warning(f"Cannot set visibility for non-existent layer: {name}")

    def compose(self) -> Surface:
        """Compose all visible layers into a single surface.

        Layers are composited in z-index order (low to high), with each
        layer's blend mode and transform applied. Only dirty regions are
        recomposited for efficiency.

        Returns
        -------
        Surface
            The final composited surface.
        """
        from ornata.api.exports.definitions import Surface

        visible_layers = [layer for layer in self._layers.values() if layer.visible]
        if not visible_layers:
            logger.debug("No visible layers to compose")
            empty_surface = Surface(width=self.width, height=self.height)
            self._last_composition = empty_surface
            return empty_surface

        sorted_layers = sorted(visible_layers, key=lambda layer: layer.z_index)
        logger.log(5, f"Composing {len(sorted_layers)} layers")

        # Create result surface, potentially reusing previous composition
        if self._last_composition and not self._dirty_regions:
            # No changes, return cached result
            logger.log(5, "Returning cached composition (no dirty regions)")
            return self._last_composition

        result_surface = Surface(width=self.width, height=self.height)

        # If we have dirty regions, we need full recomposition for now
        # TODO: Implement partial recomposition for better performance
        if self._dirty_regions:
            logger.log(5, f"Recomposing due to {len(self._dirty_regions)} dirty regions")

        for layer in sorted_layers:
            try:
                self._composite_layer(result_surface, layer)
            except Exception as e:
                logger.error(f"Failed to composite layer '{layer.name}': {e}")
                from ornata.api.exports.definitions import CompositionError
                raise CompositionError(f"Composition failed for layer '{layer.name}': {e}") from e

        # Clear dirty regions after successful composition
        self._dirty_regions.clear()
        self._last_composition = result_surface

        return result_surface

    def _composite_layer(self, target: Surface, layer: Layer) -> None:
        """Composite a single layer onto the target surface.
        
        Parameters
        ----------
        target : Surface
            The target surface to composite onto.
        layer : Layer
            The layer to composite.
            
        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import BlendMode, LayerTransform
        if layer.transform is None:
            layer.transform = LayerTransform()

        if layer.blend_mode == BlendMode.REPLACE:
            target.data = layer.surface.data
        elif layer.blend_mode == BlendMode.ALPHA:
            self._blend_alpha(target, layer)
        elif layer.blend_mode == BlendMode.ADD:
            self._blend_add(target, layer)
        elif layer.blend_mode == BlendMode.MULTIPLY:
            self._blend_multiply(target, layer)
        elif layer.blend_mode == BlendMode.SCREEN:
            self._blend_screen(target, layer)
        elif layer.blend_mode == BlendMode.OVERLAY:
            self._blend_overlay(target, layer)
        else:
            logger.warning(f"Blend mode {layer.blend_mode} not implemented, using REPLACE")
            target.data = layer.surface.data

    def _blend_alpha(self, target: Surface, layer: Layer) -> None:
        """Apply alpha blending for a layer.

        Parameters
        ----------
        target : Surface
            The target surface.
        layer : Layer
            The layer to blend.

        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import PixelSurface

        if not isinstance(target, PixelSurface) or not isinstance(layer.surface, PixelSurface):
            logger.warning(f"Alpha blending requires PixelSurface, got {type(target)} and {type(layer.surface)}")
            return

        source_data = self._ensure_pixel_surface_data(layer.surface)
        target_data = target.data
        if target_data is None:
            target.data = [row[:] for row in source_data]
            return

        # Get effective opacity
        opacity = layer.transform.opacity if layer.transform else 1.0

        # Perform alpha blending pixel by pixel
        max_height = min(target.height, layer.surface.height, len(target_data), len(source_data))
        max_width = min(target.width, layer.surface.width)
        for y in range(max_height):
            target_row = target_data[y]
            source_row = source_data[y]
            for x in range(min(max_width, len(target_row), len(source_row))):
                target_r, target_g, target_b, target_a = target_row[x]
                source_r, source_g, source_b, source_a = source_row[x]

                # Apply layer opacity to source alpha
                source_a = int(source_a * opacity)

                # Alpha blending formula: C = αs * Cs + (1 - αs) * Cd
                # Where αs is source alpha, Cs is source color, Cd is destination color
                if source_a == 255:
                    blended_r = source_r
                    blended_g = source_g
                    blended_b = source_b
                    blended_a = 255
                elif source_a == 0:
                    blended_r = target_r
                    blended_g = target_g
                    blended_b = target_b
                    blended_a = target_a
                else:
                    alpha_norm = source_a / 255.0
                    inv_alpha = 1.0 - alpha_norm

                    blended_r = int(source_r * alpha_norm + target_r * inv_alpha)
                    blended_g = int(source_g * alpha_norm + target_g * inv_alpha)
                    blended_b = int(source_b * alpha_norm + target_b * inv_alpha)
                    blended_a = max(target_a, source_a)

                target_row[x] = (blended_r, blended_g, blended_b, blended_a)

        logger.log(5, f"Alpha blended layer '{layer.name}' with opacity {opacity}")

    def _blend_add(self, target: Surface, layer: Layer) -> None:
        """Apply additive blending for a layer.

        Parameters
        ----------
        target : Surface
            The target surface.
        layer : Layer
            The layer to blend.

        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import PixelSurface

        if not isinstance(target, PixelSurface) or not isinstance(layer.surface, PixelSurface):
            logger.warning(f"Additive blending requires PixelSurface, got {type(target)} and {type(layer.surface)}")
            return

        source_data = self._ensure_pixel_surface_data(layer.surface)
        target_data = target.data
        if target_data is None:
            target.data = [row[:] for row in source_data]
            return

        opacity = layer.transform.opacity if layer.transform else 1.0

        max_height = min(target.height, layer.surface.height, len(target_data), len(source_data))
        max_width = min(target.width, layer.surface.width)
        for y in range(max_height):
            target_row = target_data[y]
            source_row = source_data[y]
            for x in range(min(max_width, len(target_row), len(source_row))):
                target_r, target_g, target_b, target_a = target_row[x]
                source_r, source_g, source_b, source_a = source_row[x]

                source_r = int(source_r * opacity)
                source_g = int(source_g * opacity)
                source_b = int(source_b * opacity)
                source_a = int(source_a * opacity)

                blended_r = min(target_r + source_r, 255)
                blended_g = min(target_g + source_g, 255)
                blended_b = min(target_b + source_b, 255)
                blended_a = min(target_a + source_a, 255)

                target_row[x] = (blended_r, blended_g, blended_b, blended_a)

        logger.log(5, f"Additively blended layer '{layer.name}' with opacity {opacity}")

    def _blend_multiply(self, target: Surface, layer: Layer) -> None:
        """Apply multiplicative blending for a layer.

        Parameters
        ----------
        target : Surface
            The target surface.
        layer : Layer
            The layer to blend.

        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import PixelSurface

        if not isinstance(target, PixelSurface) or not isinstance(layer.surface, PixelSurface):
            logger.warning(f"Multiply blending requires PixelSurface, got {type(target)} and {type(layer.surface)}")
            return

        source_data = self._ensure_pixel_surface_data(layer.surface)
        target_data = target.data
        if target_data is None:
            target.data = [row[:] for row in source_data]
            return

        opacity = layer.transform.opacity if layer.transform else 1.0

        max_height = min(target.height, layer.surface.height, len(target_data), len(source_data))
        max_width = min(target.width, layer.surface.width)
        for y in range(max_height):
            target_row = target_data[y]
            source_row = source_data[y]
            for x in range(min(max_width, len(target_row), len(source_row))):
                target_r, target_g, target_b, target_a = target_row[x]
                source_r, source_g, source_b, source_a = source_row[x]

                tr, tg, tb = target_r / 255.0, target_g / 255.0, target_b / 255.0
                sr, sg, sb = source_r / 255.0, source_g / 255.0, source_b / 255.0

                blended_r = int((tr * sr) * 255.0)
                blended_g = int((tg * sg) * 255.0)
                blended_b = int((tb * sb) * 255.0)

                blended_a = int((target_a / 255.0 * source_a / 255.0) * 255.0)

                target_row[x] = (blended_r, blended_g, blended_b, blended_a)

        logger.log(5, f"Multiply blended layer '{layer.name}' with opacity {opacity}")

    def _blend_screen(self, target: Surface, layer: Layer) -> None:
        """Apply screen blending for a layer.

        Parameters
        ----------
        target : Surface
            The target surface.
        layer : Layer
            The layer to blend.

        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import PixelSurface

        if not isinstance(target, PixelSurface) or not isinstance(layer.surface, PixelSurface):
            logger.warning(f"Screen blending requires PixelSurface, got {type(target)} and {type(layer.surface)}")
            return

        source_data = self._ensure_pixel_surface_data(layer.surface)
        target_data = target.data
        if target_data is None:
            target.data = [row[:] for row in source_data]
            return

        opacity = layer.transform.opacity if layer.transform else 1.0

        max_height = min(target.height, layer.surface.height, len(target_data), len(source_data))
        max_width = min(target.width, layer.surface.width)
        for y in range(max_height):
            target_row = target_data[y]
            source_row = source_data[y]
            for x in range(min(max_width, len(target_row), len(source_row))):
                target_r, target_g, target_b, target_a = target_row[x]
                source_r, source_g, source_b, source_a = source_row[x]

                tr, tg, tb = target_r / 255.0, target_g / 255.0, target_b / 255.0
                sr, sg, sb = source_r / 255.0, source_g / 255.0, source_b / 255.0

                blended_r = int((1.0 - (1.0 - tr) * (1.0 - sr)) * 255.0)
                blended_g = int((1.0 - (1.0 - tg) * (1.0 - sg)) * 255.0)
                blended_b = int((1.0 - (1.0 - tb) * (1.0 - sb)) * 255.0)

                blended_a = int((1.0 - (1.0 - target_a / 255.0) * (1.0 - source_a / 255.0)) * 255.0)

                target_row[x] = (blended_r, blended_g, blended_b, blended_a)

        logger.log(5, f"Screen blended layer '{layer.name}' with opacity {opacity}")

    def _blend_overlay(self, target: Surface, layer: Layer) -> None:
        """Apply overlay blending for a layer.

        Parameters
        ----------
        target : Surface
            The target surface.
        layer : Layer
            The layer to blend.

        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import PixelSurface

        if not isinstance(target, PixelSurface) or not isinstance(layer.surface, PixelSurface):
            logger.warning(f"Overlay blending requires PixelSurface, got {type(target)} and {type(layer.surface)}")
            return

        source_data = self._ensure_pixel_surface_data(layer.surface)
        target_data = target.data
        if target_data is None:
            target.data = [row[:] for row in source_data]
            return

        opacity = layer.transform.opacity if layer.transform else 1.0

        max_height = min(target.height, layer.surface.height, len(target_data), len(source_data))
        max_width = min(target.width, layer.surface.width)
        for y in range(max_height):
            target_row = target_data[y]
            source_row = source_data[y]
            for x in range(min(max_width, len(target_row), len(source_row))):
                target_r, target_g, target_b, target_a = target_row[x]
                source_r, source_g, source_b, source_a = source_row[x]

                tr, tg, tb = target_r / 255.0, target_g / 255.0, target_b / 255.0
                sr, sg, sb = source_r / 255.0, source_g / 255.0, source_b / 255.0

                def overlay_blend(base: float, blend: float) -> float:
                    if base < 0.5:
                        return 2.0 * base * blend
                    return 1.0 - 2.0 * (1.0 - base) * (1.0 - blend)

                blended_r = int(overlay_blend(tr, sr) * 255.0)
                blended_g = int(overlay_blend(tg, sg) * 255.0)
                blended_b = int(overlay_blend(tb, sb) * 255.0)

                blended_a = int(overlay_blend(target_a / 255.0, source_a / 255.0) * 255.0)

                target_row[x] = (blended_r, blended_g, blended_b, blended_a)

        logger.log(5, f"Overlay blended layer '{layer.name}' with opacity {opacity}")

    def _ensure_pixel_surface_data(self, surface: PixelSurface) -> list[list[tuple[int, int, int, int]]]:
        """Ensure a PixelSurface has initialized pixel data."""
        if surface.data is None:
            surface.data = [[(0, 0, 0, 0) for _ in range(surface.width)] for _ in range(surface.height)]
        return surface.data

    def _mark_dirty_region(self, x: int, y: int, width: int, height: int) -> None:
        """Mark a region as dirty (needs recomposition).

        Parameters
        ----------
        x : int
            X coordinate of dirty region.
        y : int
            Y coordinate of dirty region.
        width : int
            Width of dirty region.
        height : int
            Height of dirty region.
        """
        # Clamp to compositor bounds
        x = max(0, min(x, self.width - 1))
        y = max(0, min(y, self.height - 1))
        width = min(width, self.width - x)
        height = min(height, self.height - y)

        if width <= 0 or height <= 0:
            return

        # Check if this region overlaps with existing dirty regions
        # For simplicity, we just add it to the list
        # TODO: Implement region merging for better performance
        self._dirty_regions.append((x, y, width, height))
        logger.log(5, f"Marked dirty region: ({x},{y}) {width}x{height}")

    def get_dirty_regions(self) -> list[tuple[int, int, int, int]]:
        """Get list of dirty regions.

        Returns
        -------
        list[tuple[int, int, int, int]]
            List of (x, y, width, height) tuples for dirty regions.
        """
        return self._dirty_regions.copy()

    def has_dirty_regions(self) -> bool:
        """Check if there are any dirty regions.

        Returns
        -------
        bool
            True if there are dirty regions.
        """
        result = len(self._dirty_regions) > 0
        return result

    def clear_dirty_regions(self) -> None:
        """Clear all dirty region markers."""
        self._dirty_regions.clear()
        logger.log(5, "Cleared all dirty regions")

    def clear_all_layers(self) -> None:
        """Remove all layers from the compositor.
        
        Returns
        -------
        None
        """
        self._layers.clear()
        logger.debug("Cleared all compositor layers")

    def get_layer_count(self) -> int:
        """Get the number of layers in the compositor.
        
        Returns
        -------
        int
            Number of layers.
        """
        result = len(self._layers)
        return result

    def get_layer_names(self) -> list[str]:
        """Get the names of all layers.
        
        Returns
        -------
        list[str]
            List of layer names.
        """
        names = list(self._layers.keys())
        return names

    def resize(self, width: int, height: int) -> None:
        """Resize the compositor target dimensions.
        
        Parameters
        ----------
        width : int
            New width in renderer units.
        height : int
            New height in renderer units.
            
        Returns
        -------
        None
        """
        if width != self.width or height != self.height:
            logger.debug(f"Resizing compositor from {self.width}x{self.height} to {width}x{height}")
            self.width = width
            self.height = height
