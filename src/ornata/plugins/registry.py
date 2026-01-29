"""Plugin registry and discovery.

Provides a runtime registration API and entry point discovery so third-party
packages can extend Ornata without import-time coupling.

Entry point contract (group: ``ornata.plugins``):
 - The entry point object must be a callable. It will be registered under the
   entry point's name. Alternatively, the object may expose a ``register``
   attribute that is a callable returning a ``(name, func)`` tuple, which will
   be registered.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

try:
    from importlib.metadata import entry_points
except Exception:
    entry_points = None

if TYPE_CHECKING:
    from collections.abc import Callable


class PluginRegistry:
    _registry: dict[str, Callable[..., Any]] = {}  # Any: plugins can return any type

    @classmethod
    def register(cls, name: str, func: Callable[..., Any]) -> None:  # Any: plugins can return any type
        """Register a plugin function under the given name."""
        cls._registry[name] = func

    @classmethod
    def get(cls, name: str) -> Callable[..., Any] | None:  # Any: plugins can return any type
        """Retrieve a registered plugin function by name."""
        return cls._registry.get(name)

    @classmethod
    def list(cls) -> list[str]:
        """Return a sorted list of all registered plugin names."""
        return sorted(cls._registry.keys())

    @classmethod
    def load_entry_points(cls, group: str = "ornata.plugins") -> int:
        """Discover and register plugins exposed via Python entry points.

        Returns the number of plugins registered from entry points.
        """
        if entry_points is None:  # runtime lacks importlib.metadata
            return 0
        try:
            eps = entry_points().select(group=group)
        except Exception:
            try:
                eps = entry_points(group=group)
            except Exception:
                return 0

        count = 0
        for ep in eps:
            try:
                obj = ep.load()
            except Exception:
                continue
            name = getattr(ep, "name", None) or getattr(obj, "__name__", None) or "plugin"
            if callable(getattr(obj, "register", None)):
                try:
                    reg = obj.register()
                except Exception:
                    reg = None
                if isinstance(reg, tuple) and len(reg) == 2 and callable(reg[1]):
                    cls._registry[str(reg[0])] = reg[1]
                    count += 1
                    continue
            if callable(obj):
                cls._registry[str(name)] = obj
                count += 1
        return count

    def register_component(self, name: str, func: Callable[..., Any]) -> None:  # Any: plugins can return any type
        """Register a component plugin function under the given name."""
        self._registry[name] = func

    def register_renderer(self, name: str, func: Callable[..., Any]) -> None:  # Any: plugins can return any type
        """Register a renderer plugin function under the given name."""
        self._registry[name] = func

    def register_layout(self, name: str, func: Callable[..., Any]) -> None:  # Any: plugins can return any type
        """Register a layout plugin function under the given name."""
        self._registry[name] = func
