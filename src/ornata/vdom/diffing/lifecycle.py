# vdom/diffing/lifecycle.py
"""Component lifecycle management for VDOM."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.api.exports.definitions import Component

logger = get_logger(__name__)


class ComponentLifecycle:
    """Manages component lifecycle events in VDOM."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._mounted_components: dict[str, Component] = {}
        self._unmounting_components: set[str] = set()

    def mount_component(self, key: str, component: Component) -> None:
        """Mount a component."""
        with self._lock:
            if key in self._mounted_components:
                logger.warning("Component '%s' is already mounted, skipping", key)
                return

            self._mounted_components[key] = component
            logger.debug("Mounted component '%s'", key)

            # Schedule mount lifecycle (effects phase)
            self._trigger_mount(component)

    def unmount_component(self, key: str) -> None:
        """Unmount a component."""
        with self._lock:
            if key not in self._mounted_components:
                logger.warning("Component '%s' is not mounted, skipping unmount", key)
                return

            component = self._mounted_components[key]
            self._unmounting_components.add(key)

            # Schedule unmount lifecycle (effects phase)
            self._trigger_unmount(component)

            del self._mounted_components[key]
            self._unmounting_components.remove(key)
            logger.debug("Unmounted component '%s'", key)

    def update_component(self, key: str, new_component: Component) -> None:
        """Update a component."""
        with self._lock:
            if key not in self._mounted_components:
                logger.warning("Component '%s' is not mounted, skipping update", key)
                return

            old_component = self._mounted_components[key]

            # Schedule update lifecycle (effects phase)
            self._trigger_update(old_component, new_component)

            self._mounted_components[key] = new_component
            logger.debug("Updated component '%s'", key)

    def is_mounted(self, key: str) -> bool:
        """Check if a component is mounted."""
        with self._lock:
            return key in self._mounted_components

    def get_mounted_components(self) -> list[Any]:
        """Get all mounted components."""
        with self._lock:
            return list(self._mounted_components.values())

    def _trigger_mount(self, component: Component) -> None:
        """Queue component mount lifecycle as an effect."""
        from ornata.vdom.diffing.scheduler import get_scheduler
        cb: Callable[[], Any] | None = getattr(component, "on_mount", None)
        if callable(cb):
            try:
                sch = get_scheduler()
                sch.on_component_mounted(
                    label=f"on_mount:{getattr(component, 'component_name', type(component).__name__)}",
                    cb=cb,
                )
                logger.log(
                    5,
                    "Queued on_mount for %s",
                    getattr(component, "component_name", type(component).__name__),
                )  # TRACE
            except Exception as e:
                logger.error(
                    "Error queuing on_mount for %s: %s",
                    getattr(component, "component_name", type(component).__name__),
                    e,
                )

    def _trigger_unmount(self, component: Component) -> None:
        """Queue component unmount lifecycle as a high-priority effect."""
        from ornata.vdom.diffing.scheduler import get_scheduler
        cb: Callable[[], Any] | None = getattr(component, "on_unmount", None)
        if callable(cb):
            try:
                sch = get_scheduler()
                # Use enqueue_effect directly to force high priority (0)
                sch.enqueue_effect(
                    cb,
                    priority=0,
                    label=f"on_unmount:{getattr(component, 'component_name', type(component).__name__)}",
                )
                logger.log(
                    5,
                    "Queued on_unmount for %s",
                    getattr(component, "component_name", type(component).__name__),
                )  # TRACE
            except Exception as e:
                logger.error(
                    "Error queuing on_unmount for %s: %s",
                    getattr(component, "component_name", type(component).__name__),
                    e,
                )

    def _trigger_update(self, old_component: Component, new_component: Component) -> None:
        """Queue component update lifecycle as an effect."""
        from ornata.vdom.diffing.scheduler import get_scheduler
        cb: Callable[[Component], Any] | None = getattr(new_component, "on_update", None)
        if callable(cb):
            try:
                # Wrap to pass old_component at execution time
                def _runner(old: Any, func: Callable[[Any], Any]) -> None:
                    func(old)

                sch = get_scheduler()
                sch.on_component_updated(
                    label=f"on_update:{getattr(new_component, 'component_name', type(new_component).__name__)}",
                    cb=_runner,
                )
                logger.log(
                    5,
                    "Queued on_update for %s",
                    getattr(new_component, "component_name", type(new_component).__name__),
                )  # TRACE
            except Exception as e:
                logger.error(
                    "Error queuing on_update for %s: %s",
                    getattr(new_component, "component_name", type(new_component).__name__),
                    e,
                )
