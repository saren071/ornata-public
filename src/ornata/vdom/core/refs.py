"""Component reference management for VDOM."""

from __future__ import annotations

import threading
import weakref
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Component

logger = get_logger(__name__)


class ComponentRefs:
    """Manages weak references to components in VDOM."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._refs: dict[str, weakref.ReferenceType[Any]] = {}

    def add_ref(self, key: str, component: Component) -> None:
        """Add a weak reference to a component."""
        with self._lock:
            self._refs[key] = weakref.ref(component)
            logger.debug(f"Added weak reference for component '{key}'")

    def get_ref(self, key: str) -> Any | None:
        """Get a component by weak reference."""
        with self._lock:
            ref = self._refs.get(key)
            if ref is None:
                return None

            component = ref()
            if component is None:
                # Reference is dead, clean it up
                del self._refs[key]
                logger.debug(f"Cleaned up dead reference for component '{key}'")

            return component

    def remove_ref(self, key: str) -> None:
        """Remove a weak reference."""
        with self._lock:
            if key in self._refs:
                del self._refs[key]
                logger.debug(f"Removed weak reference for component '{key}'")

    def cleanup_dead_refs(self) -> int:
        """Clean up dead weak references."""
        with self._lock:
            dead_keys: list[str] = []
            for key, ref in self._refs.items():
                if ref() is None:
                    dead_keys.append(key)

            for key in dead_keys:
                del self._refs[key]

            if dead_keys:
                logger.debug(f"Cleaned up {len(dead_keys)} dead component references")

            return len(dead_keys)

    def get_all_keys(self) -> list[str]:
        """Get all reference keys."""
        with self._lock:
            return list(self._refs.keys())

    def get_live_refs_count(self) -> int:
        """Get count of live references."""
        with self._lock:
            live_count = 0
            for ref in self._refs.values():
                if ref() is not None:
                    live_count += 1
            return live_count
