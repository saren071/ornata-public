"""Particle engine for managing particle systems."""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING

from ornata.api.exports.definitions import RenderOutput
from ornata.api.exports.utils import get_logger
from ornata.effects.particles.emitter import ParticleEmitter

if TYPE_CHECKING:
    from ornata.definitions.enums import BackendTarget
    from ornata.effects.particles.config import ParticleSystemConfig
    from ornata.effects.particles.emitter import Particle

logger = get_logger(__name__)


class ParticleEngine:
    """Engine for managing particle systems with thread-safe operations.

    Provides centralized management of particle systems including creation,
    updating, rendering, and cleanup. Supports multiple concurrent particle
    systems with proper synchronization for Python 3.14 free threading.
    """

    def __init__(self) -> None:
        """Initialize the particle engine with thread-safe operations."""
        self._systems: dict[str, ParticleEmitter] = {}
        self._physics: dict[str, ParticleEmitter] = {}  # Maps to same emitter for now
        self._renderer = None  # Lazy initialization
        self._lock = threading.RLock()
        self._running = False
        self._update_thread: threading.Thread | None = None
        self._system_counter = 0

        logger.debug("Initialized particle engine")

    def create_system(self, config: ParticleSystemConfig) -> str:
        """Create a new particle system with emitter and physics setup.

        Args:
            config: Configuration dictionary for the particle system containing
                   emitter and physics parameters.

        Returns:
            Unique system identifier.

        Raises:
            ValueError: If configuration is invalid or missing required parameters.
        """

        with self._lock:
            # Generate unique system ID
            self._system_counter += 1
            system_id = f"particle_system_{self._system_counter}"

            try:
                # Create particle emitter with configuration
                emitter = ParticleEmitter(config)
                self._systems[system_id] = emitter

                # Physics is applied during update, not stored separately

                logger.debug(f"Created particle system: {system_id} at position {config.position}")
                return system_id

            except Exception as e:
                logger.error(f"Failed to create particle system '{system_id}': {e}")
                # Clean up any partial state
                if system_id in self._systems:
                    del self._systems[system_id]
                raise ValueError(f"Invalid particle system configuration: {e}") from e

    def destroy_system(self, system_id: str) -> None:
        """Destroy a particle system.

        Args:
            system_id: Identifier of the system to destroy.

        Raises:
            ParticleSystemNotFoundError: If system doesn't exist.
        """
        with self._lock:
            if system_id not in self._systems:
                from ornata.api.exports.definitions import ParticleSystemNotFoundError

                raise ParticleSystemNotFoundError(f"Particle system '{system_id}' not found")

            del self._systems[system_id]
            if system_id in self._physics:
                del self._physics[system_id]
            logger.debug(f"Destroyed particle system: {system_id}")

    def update_systems(self, delta_time: float) -> None:
        """Update all active particle systems with physics simulation.

        Args:
            delta_time: Time elapsed since last update in seconds.
        """
        from ornata.effects.particles.physics import ParticlePhysics

        with self._lock:
            updated_systems = 0
            total_particles = 0

            for system_id, emitter in self._systems.items():
                try:
                    # Update emitter (particle emission and lifecycle)
                    emitter.update(delta_time)

                    # Apply physics to particles using the emitter's config
                    physics = ParticlePhysics(emitter.config.physics)
                    physics.apply_physics(emitter.particles, delta_time)

                    particle_count = emitter.get_particle_count()
                    total_particles += particle_count
                    updated_systems += 1

                    logger.debug(f"Updated particle system {system_id} with {particle_count} particles")
                except Exception as e:
                    logger.warning(f"Failed to update particle system {system_id}: {e}")

            logger.debug(f"Updated {updated_systems} systems with {total_particles} total particles")

    def render_particles(self, backend_target: BackendTarget) -> RenderOutput:
        """Render all active particle systems using the specified renderer.

        Args:
            backend_target: Target backend for output.

        Returns:
            RenderOutput containing rendered content and metadata.
        """
        from ornata.effects.particles.renderer import ParticleRenderer

        with self._lock:
            # Lazy initialize renderer
            if self._renderer is None:
                self._renderer = ParticleRenderer()

            all_particles: list[Particle] = []
            for emitter in self._systems.values():
                all_particles.extend(emitter.particles)

            if all_particles:
                output = self._renderer.render_particles(all_particles, backend_target)
                logger.debug(f"Rendered {len(all_particles)} particles across {len(self._systems)} systems to {backend_target.value}")
                return output
            else:
                logger.debug("No particles to render")
                # Return empty render output
                return RenderOutput(content="", backend_target=backend_target.value, metadata={"particle_count": 0})

    def get_system(self, system_id: str) -> ParticleEmitter | None:
        """Get a particle system by ID.

        Args:
            system_id: Identifier of the system to retrieve.

        Returns:
            The particle emitter instance, or None if not found.
        """
        with self._lock:
            return self._systems.get(system_id)

    def start_auto_update(self, update_rate: float = 60.0) -> None:
        """Start automatic particle system updates.

        Args:
            update_rate: Updates per second.
        """
        if self._running:
            return

        self._running = True
        self._update_thread = threading.Thread(target=self._auto_update_loop, args=(update_rate,), daemon=True)
        self._update_thread.start()
        logger.debug(f"Started auto-update loop at {update_rate} FPS")

    def stop_auto_update(self) -> None:
        """Stop automatic particle system updates."""
        self._running = False
        if self._update_thread:
            self._update_thread.join(timeout=1.0)
            self._update_thread = None
        logger.debug("Stopped auto-update loop")

    def _auto_update_loop(self, update_rate: float) -> None:
        """Main update loop for automatic particle updates."""
        frame_time = 1.0 / update_rate
        last_time = time.perf_counter()

        while self._running:
            current_time = time.perf_counter()
            delta_time = current_time - last_time
            last_time = current_time

            self.update_systems(delta_time)

            # Sleep to maintain frame rate
            sleep_time = max(0, frame_time - (time.perf_counter() - current_time))
            time.sleep(sleep_time)
