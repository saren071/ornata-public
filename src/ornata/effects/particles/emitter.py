"""Particle emitters for creating and managing particle systems."""

from __future__ import annotations

import random
import threading
from typing import TYPE_CHECKING

from ornata.api.exports.definitions import Particle
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.effects.particles.config import ParticleSystemConfig

logger = get_logger(__name__)


class ParticleEmitter:
    """Emitter for creating and managing particles with thread-safe operations.

    The ParticleEmitter manages the lifecycle of particles, including emission,
    updating, and cleanup. It supports various emission patterns and particle
    properties with configurable variations.

    Attributes:
        config: Particle system configuration
        particles: List of active particles
    """

    def __init__(self, config: ParticleSystemConfig) -> None:
        """Initialize the particle emitter.

        Args:
            config: Configuration for the particle system.
        """
        self.config = config
        self.particles: list[Particle] = []
        self._lock = threading.RLock()
        self._active = True
        self._time_accumulator = 0.0

        logger.debug(f"Initialized particle emitter with config: position={config.position}, "
                    f"emission_rate={config.emission_rate}, max_particles={config.max_particles}")

    def update(self, delta_time: float) -> None:
        """Update the emitter and its particles.

        Args:
            delta_time: Time elapsed since last update in seconds.
        """
        with self._lock:
            if not self._active:
                return

            # Emit new particles
            self._time_accumulator += delta_time
            particles_to_emit = int(self._time_accumulator * self.config.emission_rate)
            self._time_accumulator -= particles_to_emit / self.config.emission_rate

            for _ in range(particles_to_emit):
                if len(self.particles) < self.config.max_particles:
                    self._emit_particle()

            # Update existing particles
            alive_particles: list[Particle] = []
            for particle in self.particles:
                particle.life -= delta_time
                if particle.life > 0:
                    # Update physics (basic integration, physics system handles complex forces)
                    particle.x += particle.vx * delta_time
                    particle.y += particle.vy * delta_time
                    particle.rotation += particle.rotation_speed * delta_time
                    alive_particles.append(particle)

            self.particles = alive_particles

            logger.debug(f"Updated {len(self.particles)} particles, emitted {particles_to_emit} new particles")

    def _emit_particle(self) -> None:
        """Emit a single particle with configured properties and variations."""
        # Calculate initial velocity with variation
        base_vx, base_vy = self.config.speed
        variation = random.uniform(-self.config.speed_variation, self.config.speed_variation)
        vx = base_vx + random.uniform(-variation, variation)
        vy = base_vy + random.uniform(-variation, variation)

        # Calculate size with variation
        size = self.config.size + random.uniform(-self.config.size_variation, self.config.size_variation)

        # Calculate color with variation
        r, g, b, a = self.config.color
        color_variation = int(self.config.color_variation)
        color = (
            max(0, min(255, r + random.randint(-color_variation, color_variation))),
            max(0, min(255, g + random.randint(-color_variation, color_variation))),
            max(0, min(255, b + random.randint(-color_variation, color_variation))),
            a,
        )

        # Calculate rotation speed with variation
        rotation_speed = self.config.rotation_speed + random.uniform(-self.config.rotation_variation, self.config.rotation_variation)

        particle = Particle(
            x=self.config.position[0],
            y=self.config.position[1],
            vx=vx,
            vy=vy,
            life=self.config.lifetime,
            max_life=self.config.lifetime,
            size=size,
            color=color,
            rotation=0.0,
            rotation_speed=rotation_speed,
        )

        self.particles.append(particle)
        logger.debug(f"Emitted particle at ({particle.x}, {particle.y}) with velocity ({vx}, {vy})")

    def set_active(self, active: bool) -> None:
        """Set whether the emitter is active.

        Args:
            active: Whether to activate the emitter.
        """
        with self._lock:
            self._active = active
            logger.debug(f"Particle emitter active state set to: {active}")

    def clear_particles(self) -> None:
        """Clear all particles from the emitter."""
        with self._lock:
            particle_count = len(self.particles)
            self.particles.clear()
            logger.debug(f"Cleared {particle_count} particles from emitter")

    def get_particle_count(self) -> int:
        """Get the current number of active particles.

        Returns:
            Number of active particles.
        """
        with self._lock:
            return len(self.particles)

    def is_active(self) -> bool:
        """Check if the emitter is currently active.

        Returns:
            True if the emitter is active, False otherwise.
        """
        with self._lock:
            return self._active
