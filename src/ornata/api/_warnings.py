"""Shared warning helpers for discouraging direct internal imports."""

from __future__ import annotations

import builtins
import warnings
from typing import Any

_warn_on_internal_imports = False
_ORIGINAL_IMPORT = builtins.__import__
_internal_warnings_installed = False


def get_internal_warnings_enabled() -> bool:
    """Return whether internal-import warnings are currently enabled."""

    return _warn_on_internal_imports


def set_internal_warnings_enabled(enabled: bool) -> None:
    """Toggle whether direct internal imports trigger warnings.

    Parameters
    ----------
    enabled : bool
        When True, import hooks emit a UserWarning for private modules.

    Returns
    -------
    None
    """

    global _warn_on_internal_imports
    _warn_on_internal_imports = enabled


def setup_internal_warnings() -> None:
    """Install an import hook that warns when private modules are imported directly."""

    global _internal_warnings_installed
    if _internal_warnings_installed:
        return

    def _warn_on_internal_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if (
            _warn_on_internal_imports
            and name.startswith("ornata.")
            and not name.startswith("ornata.api.")
        ):
            warnings.warn(
                f"Direct access to '{name}' is discouraged; prefer the ornata.api surface.",
                UserWarning,
                stacklevel=2,
            )
        return _ORIGINAL_IMPORT(name, *args, **kwargs)

    builtins.__import__ = _warn_on_internal_import
    _internal_warnings_installed = True


__all__ = [
    "get_internal_warnings_enabled",
    "set_internal_warnings_enabled",
    "setup_internal_warnings",
]
