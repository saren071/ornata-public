"""Runtime helpers for accessing the shared event subsystem."""

from __future__ import annotations

from ornata.api.exports.events import EventSubsystem
from ornata.api.exports.utils import get_logger, lock

logger = get_logger(__name__)

_event_subsystem: EventSubsystem | None = None
_event_lock = lock.Lock()


def get_event_subsystem() -> EventSubsystem:
    """Return the process-wide :class:`EventSubsystem`.

    Returns:
        EventSubsystem: Shared subsystem instance.
    """
    global _event_subsystem

    subsystem = _event_subsystem
    if subsystem is not None:
        return subsystem

    with _event_lock:
        if _event_subsystem is None:
            new_subsystem = EventSubsystem()
            new_subsystem.initialize()
            _event_subsystem = new_subsystem
        subsystem = _event_subsystem

    return subsystem


__all__ = [
    "get_event_subsystem",
]
