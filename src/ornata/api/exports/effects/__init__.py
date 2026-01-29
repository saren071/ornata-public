"""Auto-generated lazy exports for the effects subsystem."""

from __future__ import annotations

from importlib import import_module

from ornata.api._warnings import setup_internal_warnings

setup_internal_warnings()

_EXPORT_TARGETS: dict[str, str] = {
    "animation": "ornata.effects:animation",
    "particles": "ornata.effects:particles",
    "transitions": "ornata.effects:transitions",
    "coordinator": "ornata.effects.animation:coordinator",
    "easing": "ornata.effects.animation:easing",
    "interfaces": "ornata.effects.animation:interfaces",
    "keyframes": "ornata.effects.animation:keyframes",
    "timeline": "ornata.effects.animation:timeline",
    "AnimationCoordinator": "ornata.effects.animation.coordinator:AnimationCoordinator",
    "AnimationSequence": "ornata.effects.animation.coordinator:AnimationSequence",
    "ease_in_back": "ornata.effects.animation.easing:ease_in_back",
    "ease_in_bounce": "ornata.effects.animation.easing:ease_in_bounce",
    "ease_in_circ": "ornata.effects.animation.easing:ease_in_circ",
    "ease_in_cubic": "ornata.effects.animation.easing:ease_in_cubic",
    "ease_in_elastic": "ornata.effects.animation.easing:ease_in_elastic",
    "ease_in_expo": "ornata.effects.animation.easing:ease_in_expo",
    "ease_in_out_back": "ornata.effects.animation.easing:ease_in_out_back",
    "ease_in_out_bounce": "ornata.effects.animation.easing:ease_in_out_bounce",
    "ease_in_out_circ": "ornata.effects.animation.easing:ease_in_out_circ",
    "ease_in_out_cubic": "ornata.effects.animation.easing:ease_in_out_cubic",
    "ease_in_out_elastic": "ornata.effects.animation.easing:ease_in_out_elastic",
    "ease_in_out_expo": "ornata.effects.animation.easing:ease_in_out_expo",
    "ease_in_out_quad": "ornata.effects.animation.easing:ease_in_out_quad",
    "ease_in_out_quart": "ornata.effects.animation.easing:ease_in_out_quart",
    "ease_in_out_sine": "ornata.effects.animation.easing:ease_in_out_sine",
    "ease_in_quad": "ornata.effects.animation.easing:ease_in_quad",
    "ease_in_quart": "ornata.effects.animation.easing:ease_in_quart",
    "ease_in_sine": "ornata.effects.animation.easing:ease_in_sine",
    "ease_out_back": "ornata.effects.animation.easing:ease_out_back",
    "ease_out_bounce": "ornata.effects.animation.easing:ease_out_bounce",
    "ease_out_circ": "ornata.effects.animation.easing:ease_out_circ",
    "ease_out_cubic": "ornata.effects.animation.easing:ease_out_cubic",
    "ease_out_elastic": "ornata.effects.animation.easing:ease_out_elastic",
    "ease_out_expo": "ornata.effects.animation.easing:ease_out_expo",
    "ease_out_quad": "ornata.effects.animation.easing:ease_out_quad",
    "ease_out_quart": "ornata.effects.animation.easing:ease_out_quart",
    "ease_out_sine": "ornata.effects.animation.easing:ease_out_sine",
    "linear_easing": "ornata.effects.animation.easing:linear_easing",
    "FadeInAnimation": "ornata.effects.animation.effects:FadeInAnimation",
    "GradientPulseAnimation": "ornata.effects.animation.effects:GradientPulseAnimation",
    "ParticleTrailAnimation": "ornata.effects.animation.effects:ParticleTrailAnimation",
    "PulseAnimation": "ornata.effects.animation.effects:PulseAnimation",
    "ShakeAnimation": "ornata.effects.animation.effects:ShakeAnimation",
    "TypewriterAnimation": "ornata.effects.animation.effects:TypewriterAnimation",
    "WaveAnimation": "ornata.effects.animation.effects:WaveAnimation",
    "AnimationEngine": "ornata.effects.animation.engine:AnimationEngine",
    "AnimationEvent": "ornata.effects.animation.events:AnimationEvent",
    "AnimationEventDispatcher": "ornata.effects.animation.events:AnimationEventDispatcher",
    "AnimationEventType": "ornata.effects.animation.events:AnimationEventType",
    "dispatch_animation_event": "ornata.effects.animation.events:dispatch_animation_event",
    "get_event_dispatcher": "ornata.effects.animation.events:get_event_dispatcher",
    "_get_animation_engine": "ornata.effects.animation.interfaces:_get_animation_engine",
    "animate_component": "ornata.effects.animation.interfaces:animate_component",
    "create_timeline": "ornata.effects.animation.interfaces:create_timeline",
    "get_active_animations": "ornata.effects.animation.interfaces:get_active_animations",
    "get_timeline": "ornata.effects.animation.interfaces:get_timeline",
    "pause_animation": "ornata.effects.animation.interfaces:pause_animation",
    "resume_animation": "ornata.effects.animation.interfaces:resume_animation",
    "start_animation": "ornata.effects.animation.interfaces:start_animation",
    "stop_animation": "ornata.effects.animation.interfaces:stop_animation",
    "update_animations": "ornata.effects.animation.interfaces:update_animations",
    "AnimationDirection": "ornata.effects.animation.keyframes:AnimationDirection",
    "AnimationState": "ornata.effects.animation.keyframes:AnimationState",
    "AnimationBatcher": "ornata.effects.animation.optimization:AnimationBatcher",
    "AnimationOptimizer": "ornata.effects.animation.optimization:AnimationOptimizer",
    "AnimationScheduler": "ornata.effects.animation.timeline:AnimationScheduler",
    "ScheduledCallback": "ornata.effects.animation.timeline:ScheduledCallback",
    "emitter": "ornata.effects.particles:emitter",
    "physics": "ornata.effects.particles:physics",
    "ParticleSystemConfig": "ornata.effects.particles.config:ParticleSystemConfig",
    "ParticleEffects": "ornata.effects.particles.effects:ParticleEffects",
    "Particle": "ornata.effects.particles.emitter:Particle",
    "ParticleEmitter": "ornata.effects.particles.emitter:ParticleEmitter",
    "ParticleEngine": "ornata.effects.particles.engine:ParticleEngine",
    "create_particle_effect": "ornata.effects.particles.interfaces:create_particle_effect",
    "destroy_particle_effect": "ornata.effects.particles.interfaces:destroy_particle_effect",
    "get_active_particle_systems": "ornata.effects.particles.interfaces:get_active_particle_systems",
    "get_particle_engine": "ornata.effects.particles.interfaces:get_particle_engine",
    "get_particle_system": "ornata.effects.particles.interfaces:get_particle_system",
    "optimize_particle_systems": "ornata.effects.particles.interfaces:optimize_particle_systems",
    "render_particles": "ornata.effects.particles.interfaces:render_particles",
    "update_particles": "ornata.effects.particles.interfaces:update_particles",
    "ParticleOptimization": "ornata.effects.particles.optimization:ParticleOptimization",
    "ParticlePhysics": "ornata.effects.particles.physics:ParticlePhysics",
    "ParticleRenderer": "ornata.effects.particles.renderer:ParticleRenderer",
    "FrameCache": "ornata.effects.timeline:FrameCache",
    "BaseTimeline": "ornata.effects.timeline:BaseTimeline",
    "_lerp": "ornata.effects.transitions:_lerp",
    "ease_in_out": "ornata.effects.transitions:ease_in_out",
    "Timeline": "ornata.effects.animation.timeline:Timeline",
}

_RESOLVED_EXPORTS: dict[str, object] = {}

__all__ = ["__getattr__"]

def _load_target(name: str) -> object:
    """Load and cache ``name`` for this subsystem.

    Parameters
    ----------
    name : str
        Export name to resolve.

    Returns
    -------
    object
        Resolved attribute from the owning module.

    Raises
    ------
    AttributeError
        If ``name`` is unknown to this subsystem.
    """

    target = _EXPORT_TARGETS.get(name)
    if target is None:
        raise AttributeError(
            "module 'ornata.api.exports.effects' has no attribute {name!r}"
        )
    module_name, _, attr_name = target.partition(':')
    module = import_module(module_name)
    value = getattr(module, attr_name)
    _RESOLVED_EXPORTS[name] = value
    globals()[name] = value
    return value

def __getattr__(name: str) -> object:
    """Resolve an export attribute on first access.

    Parameters
    ----------
    name : str
        Export name requested from this module.

    Returns
    -------
    object
        Resolved export value.

    Raises
    ------
    AttributeError
        If ``name`` is not part of this subsystem.
    """

    if name in _RESOLVED_EXPORTS:
        return _RESOLVED_EXPORTS[name]
    return _load_target(name)

def __dir__() -> list[str]:
    """Return the sorted list of exportable names.

    Returns
    -------
    list[str]
        Sorted names available via this module.
    """

    names = ['__getattr__']
    names.extend(_EXPORT_TARGETS)
    return sorted(names)
