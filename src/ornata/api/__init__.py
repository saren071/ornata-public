"""Primary entry point for the curated Ornata public API."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from types import ModuleType

_public_exports: ModuleType | None = None
__all__: list[str] = []


def _load_public_exports() -> ModuleType:
    """Import :mod:`ornata.api.public_exports` once lazily."""

    global _public_exports, __all__
    if _public_exports is None:
        module = import_module("ornata.api.public_exports")
        _public_exports = module
        __all__ = list(getattr(module, "__all__", ()))
    return _public_exports


def __getattr__(name: str) -> Any:
    """Delegate attribute access to the curated public exports module."""

    module = _load_public_exports()
    if name == "public_exports":
        return module
    return getattr(module, name)


def __dir__() -> list[str]:
    """Return the sorted list of public export names."""

    module = _load_public_exports()
    return sorted(getattr(module, "__all__", ()))

