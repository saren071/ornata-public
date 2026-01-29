"""
# Application Exports

Convenience application-level exports for Ornata.
This module exposes the main entry point and configuration objects.

### Exports

* `Application`: The main runtime class.
* `AppConfig`: Configuration data structure.
* `BackendTarget`: Enum for rendering backends.
* `RuntimeFrame`: Context for the current frame.
"""

from __future__ import annotations

from ornata.api.exports.definitions import AppConfig, BackendTarget, RuntimeFrame
from ornata.core.application import Application

__all__ = [
    "Application",
    "AppConfig",
    "BackendTarget",
    "RuntimeFrame",
]