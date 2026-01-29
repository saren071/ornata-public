"""Auto-generated exports for ornata.effects.particles."""

from __future__ import annotations

from . import config, effects, emitter, engine, interfaces, optimization, physics, renderer
from .config import ParticleSystemConfig
from .effects import ParticleEffects
from .emitter import ParticleEmitter
from .engine import ParticleEngine
from .interfaces import (
    create_particle_effect,
    destroy_particle_effect,
    get_active_particle_systems,
    get_particle_engine,
    get_particle_system,
    optimize_particle_systems,
    render_particles,
    update_particles,
)
from .optimization import ParticleOptimization
from .physics import ParticlePhysics
from .renderer import ParticleRenderer

__all__ = [
    "ParticleEffects",
    "ParticleEmitter",
    "ParticleEngine",
    "ParticleOptimization",
    "ParticlePhysics",
    "ParticleRenderer",
    "ParticleSystemConfig",
    "config",
    "create_particle_effect",
    "destroy_particle_effect",
    "effects",
    "emitter",
    "engine",
    "get_active_particle_systems",
    "get_particle_engine",
    "get_particle_system",
    "interfaces",
    "optimization",
    "optimize_particle_systems",
    "physics",
    "render_particles",
    "renderer",
    "update_particles",
]
