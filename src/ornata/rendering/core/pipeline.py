"""Rendering pipeline orchestration.

The pipeline coordinates the flow from VDOM tree through layout calculation,
rendering, composition, and final output presentation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Bounds, Component, LayoutResult, PipelineMetrics, PipelineStage, RendererType, Surface
    from ornata.rendering.core.base_renderer import Renderer, RenderOutput
    from ornata.rendering.core.compositor import Compositor

logger = get_logger(__name__)


class RenderPipeline:
    """Orchestrates the rendering pipeline.
    
    The pipeline manages the flow from VDOM tree through layout, rendering,
    composition, and presentation stages.
    
    Parameters
    ----------
    renderer : Renderer
        The renderer to use for rendering.
    renderer_type : RendererType
        The type of renderer being used.
    use_compositor : bool
        Whether to use layer composition.
    buffer_size : int
        Number of frames to buffer (for multi-buffering).
        
    Returns
    -------
    RenderPipeline
        A rendering pipeline instance.
    """

    def __init__(
        self,
        renderer: Renderer,
        renderer_type: RendererType,
        use_compositor: bool = False,
        buffer_size: int = 2,
    ) -> None:
        """Initialize the rendering pipeline.
        
        Parameters
        ----------
        renderer : Renderer
            The renderer to use.
        renderer_type : RendererType
            The type of renderer.
        use_compositor : bool
            Whether to enable layer composition.
        buffer_size : int
            Frame buffer size.
            
        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import PipelineMetrics, PipelineStage
        from ornata.api.exports.rendering import FrameBuffer

        self.renderer = renderer
        self.renderer_type = renderer_type
        self.use_compositor = use_compositor
        self._compositor: Compositor | None = None
        self._frame_buffer = FrameBuffer(buffer_size=buffer_size)
        self._current_stage = PipelineStage.IDLE
        self._metrics = PipelineMetrics()
        self._last_error: Exception | None = None
        logger.debug(f"Initialized RenderPipeline with {renderer_type}")

    def set_compositor(self, compositor: Compositor) -> None:
        """Set the compositor for layer composition.
        
        Parameters
        ----------
        compositor : Compositor
            The compositor to use.
            
        Returns
        -------
        None
        """
        self._compositor = compositor
        self.use_compositor = True
        logger.debug("Compositor attached to pipeline")

    def render_frame(self, tree: Component, layout_result: LayoutResult, viewport_bounds: Bounds | None = None) -> RenderOutput:
        """Render a complete frame through the pipeline.

        Parameters
        ----------
        tree : Component
            The VDOM tree to render.
        layout_result : LayoutResult
            The computed layout for the tree (ignored if layout is performed).
        viewport_bounds : Bounds | None
            Viewport bounds for layout computation.

        Returns
        -------
        RenderOutput
            The final rendered output.
        """
        import time

        from ornata.api.exports.definitions import FrameStats, PipelineStage

        frame = self._frame_buffer.acquire_next_frame()
        frame.mark_rendering_start()

        try:
            self._current_stage = PipelineStage.LAYOUT
            layout_start = time.time()
            logger.log(5, f"Pipeline stage: LAYOUT (frame {frame.frame_number})")

            # Perform layout computation
            from ornata.api.exports.definitions import Bounds
            from ornata.api.exports.layout import LayoutEngine

            layout_engine = LayoutEngine()

            # Use provided viewport bounds or default
            if viewport_bounds is not None:
                container_bounds = viewport_bounds
            else:
                # Default viewport - this should ideally come from renderer capabilities
                container_bounds = Bounds(x=0, y=0, width=80, height=24)  # CLI default

            # LayoutEngine expects a BackendTarget; use the renderer's backend_target.
            layout_result = layout_engine.calculate_layout(tree, container_bounds, self.renderer.backend_target)

            layout_elapsed = time.time() - layout_start
            self._metrics.total_layout_time += layout_elapsed

            self._current_stage = PipelineStage.RENDER
            render_start = time.time()
            logger.log(5, f"Pipeline stage: RENDER (frame {frame.frame_number})")
            output = self.renderer.render_tree(tree, layout_result)
            render_elapsed = time.time() - render_start
            self._metrics.total_render_time += render_elapsed

            compose_elapsed = 0.0

            if self.use_compositor and self._compositor:
                self._current_stage = PipelineStage.COMPOSE
                compose_start = time.time()
                logger.log(5, f"Pipeline stage: COMPOSE (frame {frame.frame_number})")

                # The renderer output may provide a rendered surface attribute.
                # Use getattr to avoid hard-typing RenderOutput to a specific backend shape.
                surface = getattr(output, "surface", None)
                if surface is not None:
                    from ornata.api.exports.definitions import BlendMode
                    from ornata.api.exports.rendering import Layer

                    # Clear previous layers and add the rendered surface as a layer
                    self._compositor.clear_all_layers()
                    render_layer = Layer(
                        name="render_output",
                        surface=surface,
                        z_index=0,
                        blend_mode=BlendMode.ALPHA
                    )
                    self._compositor.add_layer(render_layer)

                    # Compose all layers
                    composed_surface: Surface = self._compositor.compose()
                    frame.surface = composed_surface
                else:
                    # No surface to compose, use render output directly
                    logger.log(5, "No surface in render output, skipping composition")
                    frame.surface = None

                compose_elapsed = time.time() - compose_start
                self._metrics.total_compose_time += compose_elapsed

            self._current_stage = PipelineStage.PRESENT
            present_start = time.time()
            logger.log(5, f"Pipeline stage: PRESENT (frame {frame.frame_number})")
            frame.mark_rendering_complete()
            present_elapsed = time.time() - present_start
            self._metrics.total_present_time += present_elapsed

            frame.mark_presented()
            self._metrics.frames_rendered += 1
            self._current_stage = PipelineStage.IDLE

            # Record frame statistics
            frame_stats = FrameStats(
                frame_number=frame.frame_number,
                layout_time=layout_elapsed,
                render_time=render_elapsed,
                compose_time=compose_elapsed if self.use_compositor and self._compositor else 0.0,
                present_time=present_elapsed,
                total_time=layout_elapsed + render_elapsed + compose_elapsed + present_elapsed,
                timestamp=time.time()
            )
            self._metrics.frame_history.append(frame_stats)

            # Keep only recent frame history (last 100 frames)
            if len(self._metrics.frame_history) > 100:
                self._metrics.frame_history.pop(0)

            return output

        except Exception as e:
            self._current_stage = PipelineStage.ERROR
            self._last_error = e
            frame.mark_dropped()
            self._metrics.frames_dropped += 1
            logger.error(f"Pipeline error in stage {self._current_stage}: {e}")
            from ornata.api.exports.definitions import PipelineError
            raise PipelineError(f"Pipeline failed at {self._current_stage}: {e}") from e

    def apply_patches(self, patches: list[Any]) -> None:
        """Apply incremental patches through the pipeline.
        
        Parameters
        ----------
        patches : list[Any]
            Patches to apply to the current render state.
            
        Returns
        -------
        None
        """
        try:
            logger.log(5, f"Applying {len(patches)} patches")
            self.renderer.apply_patches(patches)
        except Exception as e:
            logger.error(f"Failed to apply patches: {e}")
            from ornata.api.exports.definitions import PipelineError
            raise PipelineError(f"Patch application failed: {e}") from e

    def get_current_stage(self) -> PipelineStage:
        """Get the current pipeline stage.
        
        Returns
        -------
        PipelineStage
            The current stage.
        """
        return self._current_stage

    def get_metrics(self) -> PipelineMetrics:
        """Get pipeline performance metrics.
        
        Returns
        -------
        PipelineMetrics
            Performance metrics.
        """
        return self._metrics

    def get_last_error(self) -> Exception | None:
        """Get the last error that occurred.
        
        Returns
        -------
        Exception | None
            The last error, or None if no errors.
        """
        return self._last_error

    def reset_metrics(self) -> None:
        """Reset all performance metrics.
        
        Returns
        -------
        None
        """
        from ornata.api.exports.definitions import PipelineMetrics
        self._metrics = PipelineMetrics()
        logger.debug("Pipeline metrics reset")

    def clear_frame_buffer(self) -> None:
        """Clear the frame buffer.
        
        Returns
        -------
        None
        """
        self._frame_buffer.clear()
        logger.debug("Frame buffer cleared")

    def get_frame_buffer_stats(self) -> dict[str, Any]:
        """Get frame buffer statistics.
        
        Returns
        -------
        dict[str, Any]
            Frame buffer statistics.
        """
        return self._frame_buffer.get_stats()

    def is_idle(self) -> bool:
        """Check if the pipeline is idle.
        
        Returns
        -------
        bool
            True if pipeline is idle, False otherwise.
        """
        from ornata.api.exports.definitions import PipelineStage
        return self._current_stage == PipelineStage.IDLE

    def is_error(self) -> bool:
        """Check if the pipeline is in error state.
        
        Returns
        -------
        bool
            True if pipeline has an error, False otherwise.
        """
        from ornata.api.exports.definitions import PipelineStage
        return self._current_stage == PipelineStage.ERROR
