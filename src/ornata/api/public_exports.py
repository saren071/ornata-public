"""Curated public API exports for :mod:`ornata.api`."""

from __future__ import annotations

from ornata import components
from ornata.api._warnings import setup_internal_warnings
from ornata.application import Application
from ornata.definitions.dataclasses.core import AppConfig, BackendTarget, RuntimeFrame

setup_internal_warnings()

__all__ = [
    "Application",
    "AppConfig",
    "BackendTarget",
    "RuntimeFrame",
    "components",
]
