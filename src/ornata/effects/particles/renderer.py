"""Particle rendering for different output formats.

This only provides particle rendering for GPU backends."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import BackendTarget
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import RenderOutput
    from ornata.effects.particles.emitter import Particle

logger = get_logger(__name__)


class ParticleRenderer:
    """Renderer for particle systems across different backends.

    Handles rendering particles to GPU backends.

    Attributes:
        _lock: Thread synchronization lock for render operations.
    """

    def __init__(self) -> None:
        """Initialize the particle renderer with thread-safe operations."""
        self._lock = threading.RLock()
        self._render_stats = {
            "particles_rendered": 0,
            "render_calls": 0,
            "total_particles": 0,
            "average_particles_per_call": 0.0
        }

        logger.debug("Initialized particle renderer")

    def render_particles(self, particles: list[Particle], backend_target: BackendTarget, target: list[str] | None = None) -> RenderOutput:
        """Render particles to the specified renderer type.

        Args:
            particles: List of particles to render.
            renderer_type: Target renderer type for output.
            target: Optional rendering target (buffer, canvas, etc.).

        Returns:
            RenderOutput containing the rendered content and metadata.

        Raises:
            ValueError: If renderer type is not supported.
        """
        with self._lock:
            active_particles = [p for p in particles if p.life > 0]
            self._render_stats["render_calls"] += 1
            self._render_stats["total_particles"] += len(active_particles)

            if backend_target == BackendTarget.GUI:
                output = self._render_gpu(active_particles, target)
            else:
                raise ValueError(f"Unsupported backend target for particles: {backend_target}")

            self._render_stats["particles_rendered"] += len(active_particles)
            logger.debug(f"Rendered {len(active_particles)} particles to {backend_target.value}")
            return output

    def _render_gpu(self, particles: list[Particle], target: list[str] | None = None) -> RenderOutput:
        """Render particles for GUI backends.

        Args:
            particles: Active particles to render.
            target: Optional rendering target buffer.

        Returns:
            RenderOutput containing serialized particle information.
        """
        from ornata.api.exports.definitions import RenderOutput

        content_lines = [
            f"particle x={p.x:.2f} y={p.y:.2f} life={p.life:.2f} size={p.size:.2f}"
            for p in particles
        ]
        content = "\n".join(content_lines)
        if target is not None:
            target.extend(content_lines)
        return RenderOutput(content=content, backend_target=BackendTarget.GUI, metadata={"particle_count": len(particles)})

    def get_render_stats(self) -> dict[str, Any]:
        """Get rendering statistics.

        Returns:
            Dictionary with current rendering statistics.
        """
        with self._lock:
            stats = dict(self._render_stats)  # Create a copy
            if stats["render_calls"] > 0:
                stats["average_particles_per_call"] = stats["total_particles"] / stats["render_calls"]
            else:
                stats["average_particles_per_call"] = 0.0
            return stats
