"""Animation interfaces and public API."""

from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.api.exports.definitions import AnimationDirection, Component, Keyframe
    from ornata.effects.animation.engine import AnimationEngine
    from ornata.effects.animation.keyframes import Animation
    from ornata.effects.animation.timeline import Timeline

logger = get_logger(__name__)

# Global animation engine instance
_animation_engine = None


def _get_animation_engine() -> AnimationEngine:
    """Get the global animation engine instance."""
    global _animation_engine
    if _animation_engine is None:
        from ornata.effects.animation.engine import AnimationEngine
        _animation_engine = AnimationEngine()
    return _animation_engine


def animate_component(
    component: Component,
    keyframes: list[Keyframe],
    duration: float,
    *,
    easing: Callable[[float], float] | None = None,
    loop: bool | None = None,
    direction: AnimationDirection | None = None,
) -> str:
    """Animate a component with keyframes.

    Args:
        component: The component to animate.
        keyframes: List of keyframes defining the animation.
        duration: Animation duration in seconds.
        **options: Additional animation options (easing, loop, direction).

    Returns:
        Animation ID for controlling the animation.
    """
    from ornata.effects.animation.engine import AnimationEngine
    from ornata.effects.animation.keyframes import Animation

    init_kwargs: dict[str, Any] = {}
    if easing is not None:
        init_kwargs["easing"] = easing
    if loop is not None:
        init_kwargs["loop"] = loop
    if direction is not None:
        init_kwargs["direction"] = direction

    animation = Animation(component, keyframes, duration, **init_kwargs)
    engine = AnimationEngine()
    animation_id = engine.start_animation(animation)

    logger.debug(f"Started animation {animation_id} for component {component.component_name}")
    return animation_id


def stop_animation(animation_id: str) -> None:
    """Stop an animation.

    Args:
        animation_id: The animation ID to stop.
    """
    engine = _get_animation_engine()
    engine.stop_animation(animation_id)
    logger.debug(f"Stopped animation {animation_id}")


def pause_animation(animation_id: str) -> None:
    """Pause an animation.

    Args:
        animation_id: The animation ID to pause.
    """
    engine = _get_animation_engine()
    engine.pause_animation(animation_id)
    logger.debug(f"Paused animation {animation_id}")


def resume_animation(animation_id: str) -> None:
    """Resume an animation.

    Args:
        animation_id: The animation ID to resume.
    """
    engine = _get_animation_engine()
    engine.resume_animation(animation_id)
    logger.debug(f"Resumed animation {animation_id}")


def get_active_animations() -> list[Animation]:
    """Get all active animations.

    Returns:
        List of active animations.
    """
    engine = _get_animation_engine()
    return engine.get_active_animations()


def update_animations(delta_time: float) -> None:
    """Update all active animations.

    Args:
        delta_time: Time elapsed since last update.
    """
    engine = _get_animation_engine()
    engine.update_animations(delta_time)


def start_animation(animation: Animation) -> str:
    """Start an animation.

    Args:
        animation: The animation to start.

    Returns:
        Animation ID for controlling the animation.
    """
    engine = _get_animation_engine()
    animation_id = engine.start_animation(animation)

    # Dispatch animation start event
    from ornata.effects.animation.events import AnimationEventType, dispatch_animation_event
    dispatch_animation_event(AnimationEventType.ANIMATION_START, animation_id)

    return animation_id


def create_timeline(timeline_id: str) -> Timeline:
    """Create a new animation timeline.

    Args:
        timeline_id: Unique identifier for the timeline.

    Returns:
        The created timeline.
    """
    engine = _get_animation_engine()
    return engine.create_timeline(timeline_id)


def get_timeline(timeline_id: str) -> Timeline | None:
    """Get a timeline by ID.

    Args:
        timeline_id: The timeline ID to retrieve.

    Returns:
        The timeline if found, None otherwise.
    """
    engine = _get_animation_engine()
    return engine.get_timeline(timeline_id)
