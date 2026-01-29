"""Component key generation and management for VDOM."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Component

logger = get_logger(__name__)


class ComponentKeys:
    """Manages component keys for VDOM reconciliation."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._used_keys: set[str] = set()
        self._key_counter: int = 0

    def generate_key(self, component: Component, parent_key: str | None = None) -> str:
        """Generate a unique key for a component."""
        with self._lock:
            # Create a stable hash based on component properties
            component_hash = self._hash_component(component)

            # Include parent key for hierarchical uniqueness
            if parent_key:
                full_key = f"{parent_key}:{component_hash}"
            else:
                full_key = component_hash

            # Use counter-based uniqueness instead of linear search for O(1) performance
            self._key_counter += 1
            unique_key = f"{full_key}:{self._key_counter}"

            self._used_keys.add(unique_key)
            logger.debug(f"Generated key '{unique_key}' for component")
            return unique_key

    def release_key(self, key: str) -> None:
        """Release a key for reuse."""
        with self._lock:
            if key in self._used_keys:
                self._used_keys.remove(key)
                logger.debug(f"Released key '{key}'")

    def is_key_used(self, key: str) -> bool:
        """Check if a key is currently in use."""
        with self._lock:
            return key in self._used_keys

    def clear_all_keys(self) -> None:
        """Clear all used keys (for testing/debugging)."""
        with self._lock:
            count = len(self._used_keys)
            self._used_keys.clear()
            logger.debug(f"Cleared {count} component keys")

    def _hash_component(self, component: Component) -> str:
        """Create a hash string from component properties."""
        # Use faster built-in hash for better performance
        # Only use component name and a few key properties to reduce overhead
        base_hash = hash(component.component_name)

        # Add a minimal set of properties for uniqueness - reduce inspection overhead
        if hasattr(component, "__dict__"):
            # Only inspect a few key properties that significantly affect identity
            # Skip detailed property iteration for performance
            props_to_check = ["id", "key", "component_name"]
            for prop_name in props_to_check:
                if prop_name in component.__dict__:
                    base_hash ^= hash((prop_name, component.__dict__[prop_name]))

        # Convert to string with minimal processing
        return f"{base_hash & 0xFFFFFFFF:08x}"  # Use 32-bit mask for consistent length
