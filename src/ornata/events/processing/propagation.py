"""Event propagation logic for Ornata with optimized traversal."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from ornata.api.exports.definitions import Event

logger = get_logger(__name__)


class EventPropagationEngine:
    """Traverse a component tree and invoke phase-specific listeners with optimized path finding."""

    def __init__(self) -> None:
        """Initialise the propagation engine."""

        self._lock = threading.RLock()
        # Cache for frequently accessed component paths
        self._path_cache: dict[tuple[int, int], list[Any]] = {}
        self._cache_lock = threading.RLock()

    def propagate(
        self,
        event: Event,
        vdom_root: Any | None = None,
        target_component: Any | None = None,
    ) -> Event:
        """Propagate ``event`` through capture, target, and bubbling phases with optimizations."""
        # FAST PATH: no global lock for simple cases
        if self._is_simple_propagation_case(event, vdom_root, target_component):
            return self._propagate_simple(event, target_component)

        # FULL PATH: only the cache touches its own lock internally
        try:
            path = self._build_path_cached(vdom_root, target_component)
            self._run_phase("capture", event, path[:-1])
            self._run_phase("target", event, path[-1:])
            self._run_phase("bubble", event, reversed(path[:-1]))
        except Exception as exc:
            logger.error("Propagation failed for %s: %s", event.type.value, exc)
            from ornata.api.exports.definitions import EventPropagationError
            raise EventPropagationError(f"Propagation failed: {exc}") from exc

        return event

    def _is_simple_propagation_case(self, event: Event, vdom_root: Any | None, target_component: Any | None) -> bool:
        """Determine if event can use simplified propagation."""
        # Simple case: no VDOM tree or target component has no complex hierarchy
        return (
            vdom_root is None or
            target_component is None or
            not hasattr(target_component, 'parent') or
            event.type.value in ('key_down', 'key_up', 'mouse_move')  # High-frequency events
        )

    def _propagate_simple(self, event: Event, target_component: Any | None) -> Event:
        """Simplified propagation for high-frequency events."""
        if target_component is None:
            return event

        # Direct dispatch to target component only
        for listener in self._resolve_listeners_simple(target_component, event):
            if event.propagation_stopped:
                break
            try:
                listener(event)
            except Exception as exc:
                logger.warning("Simple propagation listener failure: %s", exc)

        return event

    def _run_phase(
        self,
        phase: str,
        event: Event,
        nodes: Iterable[Any],
    ) -> None:
        """Execute listeners for ``phase`` across ``nodes`` with early exit optimization.

        Args:
            phase: Phase identifier (``"capture"``, ``"target"``, or ``"bubble"``).
            event: Event to deliver to listeners.
            nodes: Iterable of nodes participating in this phase.
        """

        for node in nodes:
            if event.propagation_stopped:
                logger.log(5, "Propagation halted during %s phase", phase)
                break

            for listener in self._resolve_listeners(node, event, phase):
                try:
                    listener(event)
                except Exception as exc:
                    logger.warning("Listener failure during %s phase: %s", phase, exc)

    def _build_path_cached(self, vdom_root: Any | None, target_component: Any | None) -> list[Any]:
        """Return the node path from ``vdom_root`` to ``target_component`` with caching.

        Args:
            vdom_root: Root node of the virtual DOM tree.
            target_component: Component that originated the event.

        Returns:
            list[Any]: Ordered path from root to target. When the tree is
            unavailable the result contains the target component alone.
        """

        if vdom_root is None or target_component is None:
            return [target_component] if target_component is not None else []

        # Create cache key from object IDs
        cache_key = (id(vdom_root), id(target_component))

        with self._cache_lock:
            if cache_key in self._path_cache:
                return self._path_cache[cache_key][:]

        # Build path and cache it
        path = self._build_path_uncached(vdom_root, target_component)

        with self._cache_lock:
            self._path_cache[cache_key] = path[:]
            # Limit cache size
            if len(self._path_cache) > 1000:
                # Remove oldest entries (simple FIFO eviction)
                oldest_keys = list(self._path_cache.keys())[:100]
                for key in oldest_keys:
                    del self._path_cache[key]

        return path

    def _build_path_uncached(self, vdom_root: Any, target_component: Any) -> list[Any]:
        """Build path without caching."""
        path: list[Any] = []

        def visit(node: Any) -> bool:
            path.append(node)
            if self._node_matches(node, target_component):
                return True

            for child in getattr(node, "children", []) or []:
                if visit(child):
                    return True

            path.pop()
            return False

        if visit(vdom_root):
            return path

        logger.warning("Unable to locate target component in VDOM tree")
        return [target_component]

    def _node_matches(self, node: Any, target_component: Any) -> bool:
        """Return whether ``node`` corresponds to ``target_component``.

        Args:
            node: Current node in the traversal.
            target_component: Component being searched for.

        Returns:
            bool: ``True`` when the node matches the component.
        """

        component = getattr(node, "component", None)
        if component is target_component:
            return True

        node_component = getattr(node, "renderable", None)
        return node_component is target_component

    def _resolve_listeners(self, node: Any, event: Event, phase: str) -> list[Callable[[Event], None]]:
        """Resolve listeners registered on ``node`` for ``phase`` and ``event``.

        Args:
            node: Node from which to gather listeners.
            event: Event being propagated.
            phase: Current propagation phase.

        Returns:
            list[Callable[[Event], None]]: Ordered listeners to invoke.
        """

        listeners: list[Callable[[Event], None]] = []
        listeners.extend(self._listeners_from_mapping(node, event, phase))

        component = getattr(node, "component", None) or getattr(node, "renderable", None)
        if component is not None:
            listeners.extend(self._listeners_from_component(component, event, phase))

        return listeners

    def _resolve_listeners_simple(self, target_component: Any, event: Event) -> list[Callable[[Event], None]]:
        """Resolve listeners for simplified propagation."""
        listeners: list[Callable[[Event], None]] = []

        # Check component for direct event handlers
        hook_names = [
            f"on_{event.type.value}",
            f"handle_{event.type.value}",
            "handle_event",
        ]

        for name in hook_names:
            hook: Callable[[Event], None] | None = getattr(target_component, name, None)
            if callable(hook):
                listeners.append(hook)

        return listeners

    def _listeners_from_mapping(self, node: Any, event: Event, phase: str) -> list[Callable[[Event], None]]:
        """Extract listeners from mapping structures on ``node``.

        Args:
            node: Node potentially carrying listener mappings.
            event: Event being propagated.
            phase: Propagation phase.

        Returns:
            list[Callable[[Event], None]]: Listener callables discovered on the node.
        """

        mapping: dict[tuple[str, str], list[Callable[[Event], None]]] | None = getattr(node, "event_listeners", None)
        if not isinstance(mapping, dict):
            return []

        specific_key = (event.type.value, phase)
        listeners: list[Callable[[Event], None]] = list(mapping.get(specific_key, ()))

        wildcard_key = ("*", phase)
        listeners.extend(mapping.get(wildcard_key, ()))
        return listeners

    def _listeners_from_component(
        self,
        component: Any,
        event: Event,
        phase: str,
    ) -> list[Callable[[Event], None]]:
        """Extract listeners from component methods.

        Args:
            component: Component potentially defining event hooks.
            event: Event currently being propagated.
            phase: Propagation phase identifier.

        Returns:
            list[Callable[[Event], None]]: Component methods to invoke.
        """

        listeners: list[Callable[[Event], None]] = []

        hook_names = [
            f"on_{event.type.value}_{phase}",
            f"handle_{phase}_event",
            "handle_event",
        ]

        for name in hook_names:
            hook: Callable[[Event], None] | None = getattr(component, name, None)
            if callable(hook):
                listeners.append(hook)

        return listeners


__all__ = ["EventPropagationEngine"]