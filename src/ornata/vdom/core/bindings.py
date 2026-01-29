"""VDOM → host-object binding registry (renderer-agnostic).

This module keeps a bidirectional map:
  (RendererType, vdom_key) -> host_obj (weakref)
  id(host_obj) -> (RendererType, vdom_key)

Use this from your renderer adapters during commit/patch application to bind/unbind
host objects to VDOM keys. This lets you:
  - look up the host object for a given VDOM key (to apply props, moves, etc.)
  - route input/events from the host back to the VDOM via the reverse map
"""

from __future__ import annotations

import threading
import weakref
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import BackendTarget, StandardHostObject, VDOMTree

logger = get_logger(__name__)



class HostBindingRegistry:
    """Thread-safe registry mapping VDOM keys to backend host objects."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # (backend_target, key) -> weakref(host) or None for non-weak-referencable objects
        self._by_key: dict[tuple[BackendTarget, str], weakref.ReferenceType[Any] | None] = {}
        # id(host) -> (backend_target, key)
        self._by_host: dict[int, tuple[BackendTarget, str]] = {}
        # Strong reference fallback for host objects that cannot be weak-referenced
        self._strong_refs: dict[tuple[BackendTarget, str], StandardHostObject] = {}
        # Track host IDs for each key to clean up reverse lookups even after GC
        self._key_host_ids: dict[tuple[BackendTarget, str], int] = {}

    # ---------- Public API ----------

    def register_bind(self, backend_target: BackendTarget, key: str, host_obj: StandardHostObject) -> None:
        """Bind a host object to a VDOM key for a specific renderer."""
        with self._lock:
            tup = (backend_target, key)
            previous_host_id = self._key_host_ids.pop(tup, None)
            if previous_host_id is not None:
                self._by_host.pop(previous_host_id, None)
            force_strong = bool(getattr(host_obj, "_FORCE_STRONG_REF", False))
            # Handle objects that cannot be weak-referenced (e.g., strings, numbers, etc.)
            try:
                if force_strong:
                    raise TypeError("forced strong ref")
                ref = weakref.ref(host_obj, self._on_host_finalize)  # cleanup reverse map on GC
            except (TypeError, ValueError) as e:
                logger.debug(f"Cannot create weak reference for {type(host_obj).__name__}: {e}")
                ref = None
                self._strong_refs[tup] = host_obj
                self._by_key[tup] = None
            else:
                self._by_key[tup] = ref
                self._strong_refs.pop(tup, None)
            self._key_host_ids[tup] = id(host_obj)
            self._by_host[id(host_obj)] = (backend_target, key)
            logger.log(5, "Bound host %s ↔ key '%s' (%s)", type(host_obj).__name__, key, backend_target)  # TRACE

    def lookup_by_key(self, backend_target: BackendTarget, key: str) -> StandardHostObject | None:
        """Get the host object for a given renderer/key, or None if missing/GC'd."""
        with self._lock:
            tup = (backend_target, key)
            if tup not in self._by_key:
                return None
            ref = self._by_key[tup]
            if ref is None:
                return None
            host = ref()
            if host is None:
                # stale ref; clean
                del self._by_key[tup]
                host_id = self._key_host_ids.pop(tup, None)
                if host_id is not None:
                    self._by_host.pop(host_id, None)
                self._strong_refs.pop(tup, None)
            return host

    def lookup_key_by_host(self, host_obj: StandardHostObject) -> tuple[BackendTarget, str] | None:
        """Reverse-lookup: from a host object to (backend_target, vdom_key)."""
        with self._lock:
            return self._by_host.get(id(host_obj))

    def remove_by_key(self, backend_target: BackendTarget, key: str) -> bool:
        """Unbind host from key; returns True if something was removed."""
        with self._lock:
            tup = (backend_target, key)
            host_id = self._key_host_ids.pop(tup, None)
            ref = self._by_key.pop(tup, None)
            if ref is None:
                strong_host = self._strong_refs.pop(tup, None)
                if strong_host is not None:
                    self._by_host.pop(id(strong_host), None)
                elif host_id is not None:
                    self._by_host.pop(host_id, None)
                    return True
                return False

            target = ref()
            if target is not None:
                self._by_host.pop(id(target), None)
            elif host_id is not None:
                self._by_host.pop(host_id, None)
            logger.log(5, "Unbound key '%s' (%s)", key, backend_target)  # TRACE
            return True

    def remove_by_host(self, host_obj: StandardHostObject) -> bool:
        """Unbind by host object; returns True if removed."""
        with self._lock:
            info = self._by_host.pop(id(host_obj), None)
            if info is None:
                return False
            self._by_key.pop(info, None)
            self._strong_refs.pop(info, None)
            self._key_host_ids.pop(info, None)
            logger.log(5, "Unbound host %s", type(host_obj).__name__)  # TRACE
            return True

    def cleanup_dead(self) -> int:
        """Sweep any GC'd host refs from maps; returns number removed."""
        with self._lock:
            dead: list[tuple[BackendTarget, str]] = []
            for tup, ref in self._by_key.items():
                if ref is not None and ref() is None:
                    dead.append(tup)
            for tup in dead:
                self._by_key.pop(tup, None)
                host_id = self._key_host_ids.pop(tup, None)
                if host_id is not None:
                    self._by_host.pop(host_id, None)
            for tup in list(self._strong_refs.keys()):
                if tup not in self._by_key:
                    self._strong_refs.pop(tup, None)
                    self._key_host_ids.pop(tup, None)
            # _by_host is cleaned via weakref callback, but do a safety pass:
            _ = {idref() for idref in (ref for ref in self._by_key.values() if ref is not None) if idref() is not None}
            # Above is a defensive pattern; we won't rely on it for logic.
            return len(dead)

    def iter_bound_keys(self, backend_target: BackendTarget | None = None) -> list[tuple[BackendTarget, str]]:
        """List all bound (backend_target, key) pairs; optionally filter by backend_target."""
        with self._lock:
            if backend_target is None:
                return list(self._by_key.keys())
            return [t for t in self._by_key.keys() if t[0] == backend_target]

    def get_stats(self) -> dict[str, int]:
        """Diagnostics: count bindings and reverse entries."""
        with self._lock:
            return {"by_key": len(self._by_key), "by_host": len(self._by_host)}

    # ---------- Internal ----------

    def _on_host_finalize(self, ref: weakref.ReferenceType[Any]) -> None:
        """Weakref callback when a host object is GC'd."""
        with self._lock:
            # Remove the (backend_target,key) → host_ref entry.
            # We also need to purge _by_host, but we no longer have the host id.
            # That removal happens in remove_by_host() and in regular flows; lingering
            # entries there are harmless and get replaced on rebind.
            stale_keys = [t for t, r in self._by_key.items() if r is ref]
            for t in stale_keys:
                self._by_key.pop(t, None)
                host_id = self._key_host_ids.pop(t, None)
                if host_id is not None:
                    self._by_host.pop(host_id, None)

    # ---------- Integration helpers (optional) ----------

    def on_patch_add_node(self, tree: VDOMTree, key: str, host_obj: StandardHostObject) -> None:
        """Register ``host_obj`` when the renderer creates a concrete host for ``key``."""
        self.register_bind(tree.backend_target, key, host_obj)

    def on_patch_remove_node(self, tree: VDOMTree, key: str) -> None:
        """Unregister ``key`` when a node is removed from the renderer."""
        self.remove_by_key(tree.backend_target, key)


# Global shared registry to ensure consistent access across all modules
_registry_lock = threading.Lock()
_GLOBAL_REGISTRY: HostBindingRegistry | None = None


def get_bindings_registry() -> HostBindingRegistry:
    """Return the shared singleton bindings registry."""

    global _GLOBAL_REGISTRY
    with _registry_lock:
        if _GLOBAL_REGISTRY is None:
            _GLOBAL_REGISTRY = HostBindingRegistry()
        return _GLOBAL_REGISTRY
