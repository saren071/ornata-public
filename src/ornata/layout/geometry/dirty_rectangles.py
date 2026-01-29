"""Dirty rectangle rendering system for efficient UI updates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.definitions.dataclasses.rendering import DirtyRegion, RenderBatch

if TYPE_CHECKING:
    from types import TracebackType

    from ornata.definitions.dataclasses.layout import LayoutResult
    from ornata.definitions.protocols import RenderCallback
    from ornata.layout.engine.engine import LayoutNode


class DirtyRectangleRenderer:
    """Manages dirty rectangle rendering for efficient UI updates."""

    def __init__(self, max_batch_size: int = 50, batch_timeout: float = 0.016):  # ~60fps
        self.max_batch_size = max_batch_size
        self.batch_timeout = batch_timeout

        self.current_batch = RenderBatch()
        self.pending_batches: list[RenderBatch] = []

        self.render_callback: RenderCallback | None = None
        self.enabled = True

        # Performance tracking
        self.frames_rendered = 0
        self.total_regions_processed = 0

    def set_render_callback(self, callback: RenderCallback) -> None:
        """Set the callback function for rendering dirty rectangles."""
        self.render_callback = callback

    def mark_dirty(self, node: LayoutNode, old_layout: LayoutResult | None = None) -> None:
        """Mark a layout node as dirty and add its region to the current batch."""
        if not self.enabled:
            return

        # Calculate the dirty region
        region = self._calculate_dirty_region(node, old_layout)
        if region:
            self.current_batch.add_region(region)
            self.total_regions_processed += 1

            # Check if we should flush the batch
            if len(self.current_batch.regions) >= self.max_batch_size:
                self._flush_batch()

    def mark_region_dirty(self, x: int, y: int, width: int, height: int, priority: int = 0) -> None:
        """Mark a specific region as dirty."""
        if not self.enabled:
            return

        region = DirtyRegion(x, y, width, height, priority)
        self.current_batch.add_region(region)
        self.total_regions_processed += 1

        if len(self.current_batch.regions) >= self.max_batch_size:
            self._flush_batch()

    def flush(self) -> None:
        """Force rendering of all pending batches."""
        self._flush_batch()
        self._process_pending_batches()

    def enable(self) -> None:
        """Enable dirty rectangle rendering."""
        self.enabled = True

    def disable(self) -> None:
        """Disable dirty rectangle rendering (renders entire screen)."""
        self.enabled = False

    def get_stats(self) -> dict[str, int | float]:
        """Get performance statistics."""
        return {
            "frames_rendered": self.frames_rendered,
            "total_regions_processed": self.total_regions_processed,
            "pending_batches": len(self.pending_batches),
            "current_batch_size": len(self.current_batch.regions),
            "regions_per_frame": self.total_regions_processed / max(1, self.frames_rendered),
        }

    def _calculate_dirty_region(self, node: LayoutNode, old_layout: LayoutResult | None) -> DirtyRegion | None:
        """Calculate the dirty region for a layout node."""
        current_layout = node.layout

        if old_layout is None:
            # New node, mark entire layout as dirty
            return DirtyRegion(current_layout.x, current_layout.y, current_layout.width, current_layout.height)

        # Calculate union of old and new rectangles
        x = min(old_layout.x, current_layout.x)
        y = min(old_layout.y, current_layout.y)
        width = max(old_layout.x + old_layout.width, current_layout.x + current_layout.width) - x
        height = max(old_layout.y + old_layout.height, current_layout.y + current_layout.height) - y

        # Only mark as dirty if there's an actual change and significant difference
        if width > 0 and height > 0:
            # Calculate the area of change to prioritize larger updates
            area = width * height
            priority = min(10, area // 100)  # Scale priority based on area
            return DirtyRegion(x, y, width, height, priority)

        return None

    def _flush_batch(self) -> None:
        """Flush the current batch to pending batches."""
        if self.current_batch.regions:
            import time

            self.current_batch.timestamp = time.time()
            self.pending_batches.append(self.current_batch)
            self.current_batch = RenderBatch()

    def _process_pending_batches(self) -> None:
        """Process all pending batches."""
        import time

        current_time = time.time()

        # Process batches that are ready
        ready_batches: list[RenderBatch] = []
        remaining_batches: list[RenderBatch] = []

        for batch in self.pending_batches:
            if current_time - batch.timestamp >= self.batch_timeout:
                ready_batches.append(batch)
            else:
                remaining_batches.append(batch)

        self.pending_batches = remaining_batches

        # Render ready batches
        for batch in ready_batches:
            self._render_batch(batch)

    def _render_batch(self, batch: RenderBatch) -> None:
        """Render a single batch."""
        if self.render_callback and batch.regions:
            rectangles = batch.coalesce_regions()
            self.render_callback(rectangles)
            self.frames_rendered += 1


# Global dirty rectangle renderer instance
_dirty_renderer = DirtyRectangleRenderer()


def get_dirty_renderer() -> DirtyRectangleRenderer:
    """Get the global dirty rectangle renderer instance."""
    return _dirty_renderer


class DirtyRectangleContext:
    """Context manager for batching dirty rectangle updates."""

    def __init__(self, renderer: DirtyRectangleRenderer | None = None):
        self.renderer = renderer or get_dirty_renderer()
        self.was_enabled = self.renderer.enabled

    def __enter__(self) -> DirtyRectangleRenderer:
        # Ensure dirty rectangle rendering is enabled during the context
        self.renderer.enable()
        return self.renderer

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        # Flush any pending updates
        self.renderer.flush()
        # Restore previous enabled state
        if not self.was_enabled:
            self.renderer.disable()


def dirty_rectangles(renderer: DirtyRectangleRenderer | None = None):
    """Context manager for dirty rectangle rendering."""
    return DirtyRectangleContext(renderer)
