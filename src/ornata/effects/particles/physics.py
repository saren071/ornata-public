"""Particle physics simulation with gravity, damping, and boundary handling."""

from __future__ import annotations

import math
import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.effects.particles.emitter import Particle

logger = get_logger(__name__)


class ParticlePhysics:
    """Handles physics simulation for particles including gravity, damping, and boundaries.

    This class manages the physical simulation of particles, applying forces like gravity,
    handling damping and friction, and managing boundary conditions including bouncing
    and wrap-around behavior.

    Attributes:
        gravity: Gravity force vector (gx, gy) in units per second squared.
        damping: Velocity damping factor (0-1, where 1 is full damping).
        bounce: Bounce coefficient for boundary collisions (0-1).
        friction: Friction coefficient applied during boundary collisions (0-1).
        bounds: Boundary rectangle as (x, y, width, height) or None for no bounds.
        wrap_around: Whether particles wrap around boundaries instead of bouncing.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize particle physics with configuration.

        Args:
            config: Physics configuration dictionary containing:
                - gravity: (float, float) - Gravity vector (default: (0.0, 0.0))
                - damping: float - Velocity damping factor (default: 0.0)
                - bounce: float - Bounce coefficient (default: 0.0)
                - friction: float - Friction coefficient (default: 0.0)
                - bounds: (float, float, float, float) - Boundary rectangle (default: None)
                - wrap_around: bool - Wrap around boundaries (default: False)
        """
        self.config = config
        self._lock = threading.RLock()

        # Physics parameters with defaults
        self.gravity = config.get("gravity", (0.0, 0.0))
        self.damping = config.get("damping", 0.0)
        self.bounce = config.get("bounce", 0.0)
        self.friction = config.get("friction", 0.0)

        # Boundary settings
        self.bounds = config.get("bounds", None)  # (x, y, width, height)
        self.wrap_around = config.get("wrap_around", False)

        logger.debug(f"Initialized particle physics: gravity={self.gravity}, damping={self.damping}, "
                    f"bounce={self.bounce}, bounds={self.bounds}, wrap_around={self.wrap_around}")

    def apply_physics(self, particles: list[Particle], delta_time: float) -> None:
        """Apply physics simulation to a list of particles.

        This method updates particle velocities and positions based on configured
        physics parameters including gravity, damping, and boundary conditions.

        Args:
            particles: List of particles to update with physics.
            delta_time: Time step for simulation in seconds.
        """
        with self._lock:
            updated_count = 0
            for particle in particles:
                self._update_particle_physics(particle, delta_time)
                updated_count += 1

            logger.debug(f"Applied physics to {updated_count} particles with delta_time={delta_time}")

    def _update_particle_physics(self, particle: Particle, delta_time: float) -> None:
        """Update physics for a single particle.

        Applies gravity, damping, and integrates velocity to position.
        Then handles boundary conditions if configured.

        Args:
            particle: Particle to update.
            delta_time: Time step in seconds.
        """
        # Apply gravity acceleration to velocity
        particle.vx += self.gravity[0] * delta_time
        particle.vy += self.gravity[1] * delta_time

        # Apply velocity damping (air resistance/friction)
        if self.damping > 0:
            damping_factor = (1.0 - self.damping) ** delta_time
            particle.vx *= damping_factor
            particle.vy *= damping_factor

        # Integrate velocity to update position
        particle.x += particle.vx * delta_time
        particle.y += particle.vy * delta_time

        # Handle boundary conditions
        if self.bounds:
            self._handle_boundaries(particle)

    def _handle_boundaries(self, particle: Particle) -> None:
        """Handle boundary collisions for a particle.

        Supports both bouncing (with energy loss) and wrap-around behavior
        depending on configuration.

        Args:
            particle: Particle to check boundaries for.
        """
        if not self.bounds:
            return

        bounds_x, bounds_y, bounds_width, bounds_height = self.bounds
        max_x = bounds_x + bounds_width
        max_y = bounds_y + bounds_height

        # Check horizontal boundaries
        if particle.x < bounds_x:
            if self.wrap_around:
                particle.x = max_x - (bounds_x - particle.x)
            else:
                particle.x = bounds_x
                particle.vx = -particle.vx * self.bounce  # Reverse and dampen velocity
                particle.vy *= 1.0 - self.friction  # Apply friction to perpendicular velocity
        elif particle.x > max_x:
            if self.wrap_around:
                particle.x = bounds_x + (particle.x - max_x)
            else:
                particle.x = max_x
                particle.vx = -particle.vx * self.bounce
                particle.vy *= 1.0 - self.friction

        # Check vertical boundaries
        if particle.y < bounds_y:
            if self.wrap_around:
                particle.y = max_y - (bounds_y - particle.y)
            else:
                particle.y = bounds_y
                particle.vy = -particle.vy * self.bounce
                particle.vx *= 1.0 - self.friction
        elif particle.y > max_y:
            if self.wrap_around:
                particle.y = bounds_y + (particle.y - max_y)
            else:
                particle.y = max_y
                particle.vy = -particle.vy * self.bounce
                particle.vx *= 1.0 - self.friction

    def apply_force(self, particles: list[Particle], force: tuple[float, float], delta_time: float) -> None:
        """Apply a constant force to all particles.

        Args:
            particles: Particles to apply force to.
            force: Force vector (fx, fy) in units of acceleration.
            delta_time: Time step in seconds.
        """
        with self._lock:
            fx, fy = force
            for particle in particles:
                particle.vx += fx * delta_time
                particle.vy += fy * delta_time

            logger.debug(f"Applied force {force} to {len(particles)} particles")

    def apply_attraction(self, particles: list[Particle], center: tuple[float, float], strength: float, delta_time: float) -> None:
        """Apply gravitational attraction force towards a center point.

        Uses inverse square law with softening to avoid singularities.

        Args:
            particles: Particles to attract.
            center: Attraction center point (x, y).
            strength: Attraction strength coefficient.
            delta_time: Time step in seconds.
        """
        with self._lock:
            cx, cy = center
            for particle in particles:
                dx = cx - particle.x
                dy = cy - particle.y
                distance_squared = dx * dx + dy * dy

                if distance_squared > 0:
                    distance = math.sqrt(distance_squared)
                    # Inverse square law with epsilon softening
                    force = strength / (distance_squared + 1.0)
                    particle.vx += (dx / distance) * force * delta_time
                    particle.vy += (dy / distance) * force * delta_time

            logger.debug(f"Applied attraction to {len(particles)} particles towards {center}")

    def apply_repulsion(self, particles: list[Particle], center: tuple[float, float], strength: float, delta_time: float) -> None:
        """Apply repulsive force away from a center point.

        Uses inverse square law with softening to avoid singularities.

        Args:
            particles: Particles to repel.
            center: Repulsion center point (x, y).
            strength: Repulsion strength coefficient.
            delta_time: Time step in seconds.
        """
        with self._lock:
            cx, cy = center
            for particle in particles:
                dx = particle.x - cx
                dy = particle.y - cy
                distance_squared = dx * dx + dy * dy

                if distance_squared > 0:
                    distance = math.sqrt(distance_squared)
                    # Inverse square law with epsilon softening
                    force = strength / (distance_squared + 1.0)
                    particle.vx += (dx / distance) * force * delta_time
                    particle.vy += (dy / distance) * force * delta_time

            logger.debug(f"Applied repulsion to {len(particles)} particles away from {center}")
