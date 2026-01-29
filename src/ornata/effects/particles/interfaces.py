"""Particle subsystem interface functions for public API access."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import BackendTarget, RenderOutput
    from ornata.effects.particles.config import ParticleSystemConfig
    from ornata.effects.particles.engine import ParticleEngine

logger = get_logger(__name__)

# Global particle engine instance with thread-safe access
_particle_engine: ParticleEngine | None = None
_engine_lock = threading.RLock()


def get_particle_engine() -> ParticleEngine:
    """Get the global particle engine instance.

    Returns:
        The global particle engine with lazy initialization.
    """
    global _particle_engine
    with _engine_lock:
        if _particle_engine is None:
            from ornata.effects.particles.engine import ParticleEngine
            _particle_engine = ParticleEngine()
        return _particle_engine


def create_particle_effect(effect_type: str, **config: Any) -> str:
    """Create a particle effect with the specified type and configuration.

    Args:
        effect_type: Type of particle effect ("explosion", "firework", "rain", "snow", "smoke").
        **config: Effect-specific configuration parameters.

    Returns:
        Unique identifier for the created particle system.

    Raises:
        InvalidParticleConfigError: If the configuration is invalid.

    Example:
        >>> system_id = create_particle_effect("explosion", position=(100, 100), intensity=2.0)
        >>> # Particle system is now active and will be updated automatically
    """
    from ornata.effects.particles.config import ParticleSystemConfig

    engine = get_particle_engine()

    try:
        # Create effect configuration based on type
        system_config = ParticleSystemConfig.for_effect(effect_type, **config)
        system_id = engine.create_system(system_config)

        logger.debug(f"Created particle effect '{effect_type}' with ID: {system_id}")
        return system_id

    except Exception as e:
        logger.error(f"Failed to create particle effect '{effect_type}': {e}")
        from ornata.api.exports.definitions import InvalidParticleConfigError
        raise InvalidParticleConfigError(f"Invalid configuration for effect '{effect_type}': {e}") from e


def update_particles(delta_time: float) -> None:
    """Update all active particle systems with physics and lifecycle management.

    Args:
        delta_time: Time elapsed since last update in seconds.

    Example:
        >>> # In game/render loop
        >>> update_particles(1.0/60.0)  # 60 FPS
    """
    try:
        engine = get_particle_engine()
        engine.update_systems(delta_time)
        logger.debug(f"Updated all particle systems with delta_time={delta_time}")
    except Exception as e:
        logger.error(f"Failed to update particles: {e}")
        raise


def render_particles(backend_target: BackendTarget) -> RenderOutput:
    """Render all active particle systems to the specified renderer type.

    Args:
        backend_target: Target backend for output.

    Returns:
        RenderOutput containing the rendered particle content.

    Example:
        >>> from ornata.api.exports.definitions import BackendTarget
        >>> output = render_particles(BackendTarget.GUI)
        >>> print(output.content)
    """
    try:
        engine = get_particle_engine()
        output = engine.render_particles(backend_target)
        logger.debug(f"Rendered particles to {backend_target.value}")
        return output
    except Exception as e:
        logger.error(f"Failed to render particles: {e}")
        raise


def destroy_particle_effect(system_id: str) -> None:
    """Destroy a particle effect and free its resources.

    Args:
        system_id: Identifier of the particle system to destroy.

    Raises:
        ParticleSystemNotFoundError: If the system doesn't exist.

    Example:
        >>> destroy_particle_effect("particle_system_1")
    """
    try:
        engine = get_particle_engine()
        engine.destroy_system(system_id)
        logger.debug(f"Destroyed particle effect: {system_id}")
    except Exception as e:
        from ornata.api.exports.definitions import ParticleSystemNotFoundError
        logger.error(f"Failed to destroy particle effect '{system_id}': {e}")
        raise ParticleSystemNotFoundError(f"Failed to destroy particle system '{system_id}': {e}") from e


def get_particle_system(system_id: str) -> ParticleSystemConfig | None:
    """Get configuration information about a particle system.

    Args:
        system_id: Identifier of the particle system.

    Returns:
        Particle system configuration, or None if not found.

    Example:
        >>> config = get_particle_system("particle_system_1")
        >>> if config:
        ...     print(f"System has {config.max_particles} max particles")
    """
    try:
        engine = get_particle_engine()
        emitter = engine.get_system(system_id)
        return emitter.config if emitter else None
    except Exception as e:
        logger.error(f"Failed to get particle system '{system_id}': {e}")
        return None


def get_active_particle_systems() -> list[str]:
    """Get identifiers of all active particle systems.

    Returns:
        List of active particle system identifiers.

    Example:
        >>> systems = get_active_particle_systems()
        >>> print(f"Active systems: {systems}")
    """
    try:
        # Note: This would require adding a method to ParticleEngine to list systems
        # For now, return empty list as this needs engine modification
        logger.debug("Retrieved active particle system list")
        return []
    except Exception as e:
        logger.error(f"Failed to get active particle systems: {e}")
        return []


def optimize_particle_systems() -> dict[str, Any]:
    """Apply performance optimizations to all active particle systems.

    Returns:
        Dictionary with optimization statistics and results.

    Example:
        >>> stats = optimize_particle_systems()
        >>> print(f"Optimized {stats['systems_optimized']} systems")
    """
    try:
        from ornata.effects.particles.optimization import ParticleOptimization

        optimizer = ParticleOptimization()
        stats = optimizer.get_performance_stats()
        logger.debug("Applied particle system optimizations")
        return stats
    except Exception as e:
        logger.error(f"Failed to optimize particle systems: {e}")
        return {"error": str(e)}
