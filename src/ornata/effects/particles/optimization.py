"""Particle system optimization utilities with performance monitoring."""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.effects.particles.config import ParticleSystemConfig
    from ornata.effects.particles.emitter import Particle

logger = get_logger(__name__)


class ParticleOptimization:
    """Optimization utilities for particle systems with performance monitoring.

    Provides various optimization techniques including particle culling, batching,
    physics optimization, and performance statistics collection.
    """

    def __init__(self) -> None:
        """Initialize particle optimization with thread-safe operations."""
        self._lock = threading.RLock()
        self._performance_stats = {
            "particles_processed": 0,
            "batches_created": 0,
            "particles_culled": 0,
            "physics_optimized": 0,
            "total_time_spent": 0.0
        }

    def optimize_emitter_config(self, config: ParticleSystemConfig) -> ParticleSystemConfig:
        """Optimize particle emitter configuration for performance.

        Args:
            config: Original particle system configuration.

        Returns:
            Optimized configuration with performance constraints applied.
        """
        from ornata.effects.particles.config import ParticleSystemConfig

        with self._lock:
            start_time = time.perf_counter()

            # Apply performance optimizations
            optimized_params: dict[str, float | int] = {}

            # Optimize emission rate based on performance constraints
            if config.emission_rate > 100.0:
                optimized_params["emission_rate"] = 100.0
                logger.debug(f"Reduced emission rate from {config.emission_rate} to 100 for performance")

            # Optimize max particles
            if config.max_particles > 1000:
                optimized_params["max_particles"] = 1000
                logger.debug(f"Reduced max particles from {config.max_particles} to 1000 for performance")

            # Optimize lifetime for better performance
            if config.lifetime > 10.0:
                optimized_params["lifetime"] = 10.0
                logger.debug(f"Reduced lifetime from {config.lifetime} to 10 for performance")

            # Create optimized config
            optimized_config = config
            if optimized_params:
                # Create a new config with optimized parameters
                optimized_config = ParticleSystemConfig(
                    position=config.position,
                    emission_rate=optimized_params.get("emission_rate", config.emission_rate),
                    max_particles=int(optimized_params.get("max_particles", config.max_particles)),
                    lifetime=optimized_params.get("lifetime", config.lifetime),
                    speed=config.speed,
                    speed_variation=config.speed_variation,
                    size=config.size,
                    size_variation=config.size_variation,
                    color=config.color,
                    color_variation=config.color_variation,
                    rotation_speed=config.rotation_speed,
                    rotation_variation=config.rotation_variation,
                    physics=config.physics,
                    renderer=config.renderer
                )

            elapsed = time.perf_counter() - start_time
            self._performance_stats["total_time_spent"] += elapsed

            return optimized_config

    def batch_particles(self, particles: list[Particle], batch_size: int = 64) -> list[list[Particle]]:
        """Batch particles for efficient processing.

        Args:
            particles: List of particles to batch.
            batch_size: Maximum particles per batch.

        Returns:
            List of particle batches for optimized processing.
        """
        with self._lock:
            start_time = time.perf_counter()

            batches: list[list[Particle]] = []
            for i in range(0, len(particles), batch_size):
                batch = particles[i : i + batch_size]
                batches.append(batch)

            elapsed = time.perf_counter() - start_time
            self._performance_stats["total_time_spent"] += elapsed
            self._performance_stats["batches_created"] += len(batches)
            self._performance_stats["particles_processed"] += len(particles)

            logger.debug(f"Created {len(batches)} batches from {len(particles)} particles")
            return batches

    def cull_invisible_particles(self, particles: list[Particle], viewport: tuple[float, float, float, float]) -> list[Particle]:
        """Cull particles outside the viewport for performance optimization.

        Args:
            particles: List of particles to cull.
            viewport: Viewport rectangle as (x, y, width, height).

        Returns:
            List of visible particles within the viewport.
        """
        with self._lock:
            start_time = time.perf_counter()

            vx, vy, vw, vh = viewport
            visible: list[Particle] = []

            for particle in particles:
                # Check if particle is within viewport bounds
                if vx <= particle.x <= vx + vw and vy <= particle.y <= vy + vh:
                    visible.append(particle)

            culled_count = len(particles) - len(visible)
            if culled_count > 0:
                self._performance_stats["particles_culled"] += culled_count
                logger.debug(f"Culled {culled_count} invisible particles, {len(visible)} visible")

            elapsed = time.perf_counter() - start_time
            self._performance_stats["total_time_spent"] += elapsed

            return visible

    def optimize_physics(self, particles: list[Particle], delta_time: float) -> None:
        """Optimize physics calculations for multiple particles using grouping.

        Args:
            particles: Particles to optimize physics for.
            delta_time: Time step in seconds.
        """
        with self._lock:
            start_time = time.perf_counter()

            # Group particles by similar properties for batch processing
            groups = self._group_particles_by_properties(particles)

            for group_props, group_particles in groups.items():
                self._optimize_group_physics(group_particles, group_props, delta_time)

            elapsed = time.perf_counter() - start_time
            self._performance_stats["total_time_spent"] += elapsed
            self._performance_stats["physics_optimized"] += len(particles)

            logger.debug(f"Optimized physics for {len(particles)} particles in {len(groups)} groups")

    def _group_particles_by_properties(self, particles: list[Particle]) -> dict[tuple[float, float, float], list[Particle]]:
        """Group particles by similar physical properties for optimized processing.

        Args:
            particles: Particles to group by velocity and size.

        Returns:
            Dictionary mapping (vx, vy, size) tuples to particle lists.
        """
        groups: dict[tuple[float, float, float], list[Particle]] = {}
        for particle in particles:
            # Create a key based on physical properties that affect calculations
            key = (
                round(particle.vx, 2),  # Round to reduce key variations
                round(particle.vy, 2),
                round(particle.size, 1),
            )

            if key not in groups:
                groups[key] = []
            groups[key].append(particle)

        return groups

    def _optimize_group_physics(self, particles: list[Particle], properties: tuple[float, float, float], delta_time: float) -> None:
        """Apply optimized physics calculations for a group of similar particles.

        Args:
            particles: Group of particles with similar properties.
            properties: (vx, vy, size) tuple for the group.
            delta_time: Time step in seconds.
        """
        # For grouped particles, we can optimize by pre-calculating common values
        base_vx, base_vy, _ = properties

        for particle in particles:
            # Apply basic physics integration (gravity and physics are handled separately)
            particle.x += base_vx * delta_time
            particle.y += base_vy * delta_time

    def get_performance_stats(self) -> dict[str, Any]:
        """Get comprehensive performance statistics for optimization operations.

        Returns:
            Dictionary with detailed performance metrics and optimization status.
        """
        with self._lock:
            stats = dict(self._performance_stats)
            stats.update({
                "optimization_enabled": True,
                "batch_size": 64,
                "culling_enabled": True,
                "grouping_enabled": True,
                "average_processing_time": (
                    stats["total_time_spent"] / max(1, stats["particles_processed"])
                    if stats["particles_processed"] > 0 else 0.0
                )
            })
            return stats
