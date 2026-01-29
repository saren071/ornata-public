"""Type stubs for the effects subsystem exports."""

from __future__ import annotations

from ornata.effects import animation as animation
from ornata.effects import particles as particles
from ornata.effects import transitions as transitions
from ornata.effects.animation import Timeline as Timeline
from ornata.effects.animation import coordinator as coordinator
from ornata.effects.animation import easing as easing
from ornata.effects.animation import interfaces as interfaces
from ornata.effects.animation import keyframes as keyframes
from ornata.effects.animation import timeline as timeline
from ornata.effects.animation.coordinator import AnimationCoordinator as AnimationCoordinator
from ornata.effects.animation.coordinator import AnimationSequence as AnimationSequence
from ornata.effects.animation.easing import ease_in_back as ease_in_back
from ornata.effects.animation.easing import ease_in_bounce as ease_in_bounce
from ornata.effects.animation.easing import ease_in_circ as ease_in_circ
from ornata.effects.animation.easing import ease_in_cubic as ease_in_cubic
from ornata.effects.animation.easing import ease_in_elastic as ease_in_elastic
from ornata.effects.animation.easing import ease_in_expo as ease_in_expo
from ornata.effects.animation.easing import ease_in_out_back as ease_in_out_back
from ornata.effects.animation.easing import ease_in_out_bounce as ease_in_out_bounce
from ornata.effects.animation.easing import ease_in_out_circ as ease_in_out_circ
from ornata.effects.animation.easing import ease_in_out_cubic as ease_in_out_cubic
from ornata.effects.animation.easing import ease_in_out_elastic as ease_in_out_elastic
from ornata.effects.animation.easing import ease_in_out_expo as ease_in_out_expo
from ornata.effects.animation.easing import ease_in_out_quad as ease_in_out_quad
from ornata.effects.animation.easing import ease_in_out_quart as ease_in_out_quart
from ornata.effects.animation.easing import ease_in_out_sine as ease_in_out_sine
from ornata.effects.animation.easing import ease_in_quad as ease_in_quad
from ornata.effects.animation.easing import ease_in_quart as ease_in_quart
from ornata.effects.animation.easing import ease_in_sine as ease_in_sine
from ornata.effects.animation.easing import ease_out_back as ease_out_back
from ornata.effects.animation.easing import ease_out_bounce as ease_out_bounce
from ornata.effects.animation.easing import ease_out_circ as ease_out_circ
from ornata.effects.animation.easing import ease_out_cubic as ease_out_cubic
from ornata.effects.animation.easing import ease_out_elastic as ease_out_elastic
from ornata.effects.animation.easing import ease_out_expo as ease_out_expo
from ornata.effects.animation.easing import ease_out_quad as ease_out_quad
from ornata.effects.animation.easing import ease_out_quart as ease_out_quart
from ornata.effects.animation.easing import ease_out_sine as ease_out_sine
from ornata.effects.animation.easing import linear_easing as linear_easing
from ornata.effects.animation.effects import FadeInAnimation as FadeInAnimation
from ornata.effects.animation.effects import GradientPulseAnimation as GradientPulseAnimation
from ornata.effects.animation.effects import ParticleTrailAnimation as ParticleTrailAnimation
from ornata.effects.animation.effects import PulseAnimation as PulseAnimation
from ornata.effects.animation.effects import ShakeAnimation as ShakeAnimation
from ornata.effects.animation.effects import TypewriterAnimation as TypewriterAnimation
from ornata.effects.animation.effects import WaveAnimation as WaveAnimation
from ornata.effects.animation.engine import AnimationEngine as AnimationEngine
from ornata.effects.animation.events import AnimationEvent as AnimationEvent
from ornata.effects.animation.events import AnimationEventDispatcher as AnimationEventDispatcher
from ornata.effects.animation.events import AnimationEventType as AnimationEventType
from ornata.effects.animation.events import dispatch_animation_event as dispatch_animation_event
from ornata.effects.animation.events import get_event_dispatcher as get_event_dispatcher
from ornata.effects.animation.interfaces import _get_animation_engine as _get_animation_engine  #type: ignore
from ornata.effects.animation.interfaces import animate_component as animate_component  #type: ignore
from ornata.effects.animation.interfaces import create_timeline as create_timeline  #type: ignore
from ornata.effects.animation.interfaces import get_active_animations as get_active_animations  #type: ignore
from ornata.effects.animation.interfaces import get_timeline as get_timeline  #type: ignore
from ornata.effects.animation.interfaces import pause_animation as pause_animation  #type: ignore
from ornata.effects.animation.interfaces import resume_animation as resume_animation
from ornata.effects.animation.interfaces import start_animation as start_animation  #type: ignore
from ornata.effects.animation.interfaces import stop_animation as stop_animation
from ornata.effects.animation.interfaces import update_animations as update_animations
from ornata.effects.animation.keyframes import AnimationDirection as AnimationDirection
from ornata.effects.animation.keyframes import AnimationState as AnimationState
from ornata.effects.animation.optimization import AnimationBatcher as AnimationBatcher
from ornata.effects.animation.optimization import AnimationOptimizer as AnimationOptimizer
from ornata.effects.animation.timeline import AnimationScheduler as AnimationScheduler
from ornata.effects.animation.timeline import ScheduledCallback as ScheduledCallback
from ornata.effects.particles import emitter as emitter
from ornata.effects.particles import physics as physics
from ornata.effects.particles.config import ParticleSystemConfig as ParticleSystemConfig
from ornata.effects.particles.effects import ParticleEffects as ParticleEffects
from ornata.effects.particles.emitter import Particle as Particle
from ornata.effects.particles.emitter import ParticleEmitter as ParticleEmitter
from ornata.effects.particles.engine import ParticleEngine as ParticleEngine
from ornata.effects.particles.interfaces import create_particle_effect as create_particle_effect
from ornata.effects.particles.interfaces import destroy_particle_effect as destroy_particle_effect
from ornata.effects.particles.interfaces import get_active_particle_systems as get_active_particle_systems
from ornata.effects.particles.interfaces import get_particle_engine as get_particle_engine  #type: ignore
from ornata.effects.particles.interfaces import get_particle_system as get_particle_system  #type: ignore
from ornata.effects.particles.interfaces import optimize_particle_systems as optimize_particle_systems
from ornata.effects.particles.interfaces import render_particles as render_particles  #type: ignore
from ornata.effects.particles.interfaces import update_particles as update_particles
from ornata.effects.particles.optimization import ParticleOptimization as ParticleOptimization
from ornata.effects.particles.physics import ParticlePhysics as ParticlePhysics
from ornata.effects.particles.renderer import ParticleRenderer as ParticleRenderer
from ornata.effects.timeline import BaseTimeline as BaseTimeline
from ornata.effects.timeline import FrameCache as FrameCache
from ornata.effects.transitions import _lerp as _lerp  #type: ignore
from ornata.effects.transitions import ease_in_out as ease_in_out

__all__ = [
    "AnimationBatcher",
    "AnimationCoordinator",
    "AnimationDirection",
    "AnimationEngine",
    "AnimationEvent",
    "AnimationEventDispatcher",
    "AnimationEventType",
    "AnimationOptimizer",
    "AnimationScheduler",
    "AnimationSequence",
    "AnimationState",
    "FadeInAnimation",
    "FrameCache",
    "GradientPulseAnimation",
    "Particle",
    "ParticleEffects",
    "ParticleEmitter",
    "ParticleEngine",
    "ParticleOptimization",
    "ParticlePhysics",
    "ParticleRenderer",
    "ParticleSystemConfig",
    "ParticleTrailAnimation",
    "PulseAnimation",
    "ScheduledCallback",
    "ShakeAnimation",
    "BaseTimeline",
    "Timeline",
    "TypewriterAnimation",
    "WaveAnimation",
    "_get_animation_engine",
    "_lerp",
    "animate_component",
    "animation",
    "coordinator",
    "create_particle_effect",
    "create_timeline",
    "destroy_particle_effect",
    "dispatch_animation_event",
    "ease_in_back",
    "ease_in_bounce",
    "ease_in_circ",
    "ease_in_cubic",
    "ease_in_elastic",
    "ease_in_expo",
    "ease_in_out",
    "ease_in_out_back",
    "ease_in_out_bounce",
    "ease_in_out_circ",
    "ease_in_out_cubic",
    "ease_in_out_elastic",
    "ease_in_out_expo",
    "ease_in_out_quad",
    "ease_in_out_quart",
    "ease_in_out_sine",
    "ease_in_quad",
    "ease_in_quart",
    "ease_in_sine",
    "ease_out_back",
    "ease_out_bounce",
    "ease_out_circ",
    "ease_out_cubic",
    "ease_out_elastic",
    "ease_out_expo",
    "ease_out_quad",
    "ease_out_quart",
    "ease_out_sine",
    "easing",
    "emitter",
    "get_active_animations",
    "get_active_particle_systems",
    "get_event_dispatcher",
    "get_particle_engine",
    "get_particle_system",
    "get_timeline",
    "interfaces",
    "keyframes",
    "linear_easing",
    "optimize_particle_systems",
    "particles",
    "pause_animation",
    "physics",
    "render_particles",
    "resume_animation",
    "start_animation",
    "stop_animation",
    "timeline",
    "transitions",
    "update_animations",
    "update_particles",
]