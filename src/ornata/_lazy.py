"""
# Lazy Loading

Lazy attribute resolution helpers for the root `ornata` package.
This module intercepts attribute access to import heavy submodules only when needed.
"""

from __future__ import annotations

import sys
from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType

_LAZY_SUBMODULES: frozenset[str] = frozenset({"components", "effects", "utils"})


def __getattr__(name: str) -> ModuleType:
    """Resolve heavy subpackages on first access.

    ### Parameters
    
    * **name** (`str`): Attribute requested from `ornata`.

    ### Returns
    
    * `ModuleType`: Imported module corresponding to `name`.

    ### Raises
    
    * `AttributeError`: If the requested attribute is not a supported lazy submodule.
    """

    if name not in _LAZY_SUBMODULES:
        raise AttributeError(f"module 'ornata' has no attribute '{name}'")

    module = import_module(f"ornata.{name}")
    root = sys.modules.get("ornata")
    if root is not None:
        setattr(root, name, module)
    return module


__all__ = ["__getattr__"]