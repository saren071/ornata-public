""" Effects Dataclasses for Ornata """

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from ornata.definitions.enums import AnimationEventType

# Forward declaration for recursive type hints
Effect = Any

@dataclass(slots=True)
class Transform:
    """Animation transform."""
    translate_x: float = 0.0
    translate_y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotate: float = 0.0
    opacity: float = 1.0
    text_length: float = 0.0
    current_text: str | None = None
    positions: list[int] | None = None
    color: str | None = None
    offset: str | None = None
    gradient_text: str | None = None
    trail_text: str | None = None


@dataclass(slots=True)
class AnimationState:
    """Current state of an animation."""
    progress: float
    transforms: list[Transform] = field(default_factory=list)


@dataclass(slots=True)
class ScheduledCallback:
    """Represents a scheduled callback."""
    callback_id: str
    callback: Callable[[], None]
    scheduled_time: float
    repeating: bool
    interval: float
    next_execution: float


@dataclass(slots=True)
class Particle:
    """Represents a single particle with position, velocity, and visual properties."""
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    size: float
    color: tuple[int, int, int, int]
    rotation: float
    rotation_speed: float


@dataclass(slots=True)
class Keyframe:
    """Unified keyframe definition for animation.
    
    Can represent a CSS-style property keyframe (offset + properties)
    or a functional keyframe (time + action).
    """
    offset: float  # 0.0 to 1.0
    properties: dict[str, str | float] = field(default_factory=dict)
    action: Callable[[], None] | None = None

    def __post_init__(self) -> None:
        """Validate keyframe offset."""
        if not 0.0 <= self.offset <= 1.0:
            raise ValueError(f"Keyframe offset must be between 0.0 and 1.0, got {self.offset}")


@dataclass(slots=True, frozen=True)
class Keyframes:
    """Sequence of keyframes for an animation."""
    name: str
    keyframes: list[Keyframe]


@dataclass(slots=True, frozen=True)
class Animation:
    """Animation metadata."""
    name: str
    duration: float
    delay: float = 0.0
    iteration_count: float | str = 1
    direction: str = "normal"
    fill_mode: str = "none"
    timing_function: str = "ease"
    play_state: str = "running"


@dataclass(slots=True)
class QueuedEffect:
    cb: Effect
    priority: int = 1
    label: str | None = None
    enqueued_at: float = field(default_factory=time.monotonic)


@dataclass(slots=True)
class QueuedAsyncEffect:
    factory: Callable[[], Coroutine[Any, Any, Any]]  # factory, not a created coroutine
    priority: int = 1
    label: str | None = None
    enqueued_at: float = field(default_factory=time.monotonic)


@dataclass(slots=True)
class AnimationEvent:
    """Animation event data."""
    event_type: AnimationEventType
    animation_id: str | None = None
    sequence_id: str | None = None
    progress: float = 0.0
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        """Initialize timestamp if not provided."""
        if self.timestamp == 0.0:
            self.timestamp = time.perf_counter()


__all__ = [
    "Animation",
    "AnimationEvent",
    "AnimationState",
    "Keyframe",
    "Keyframes",
    "Particle",
    "ScheduledCallback",
    "Transform",
    "QueuedAsyncEffect",
    "QueuedEffect",
]
