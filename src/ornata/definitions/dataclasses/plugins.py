""" Plugins Dataclasses for Ornata """

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PluginMetadata:
    """Metadata for a discovered plugin."""
    name: str
    version: str
    description: str | None = None
    author: str | None = None
    license: str | None = None
    provides_components: list[str] = field(default_factory=list)
    provides_themes: list[str] = field(default_factory=list)
    provides_backends: list[str] = field(default_factory=list)
    provides_layouts: list[str] = field(default_factory=list)
    requires_python: str | None = None
    requires_ornata: str | None = None
    requires_platforms: set[str] = field(default_factory=set)
    entry_point: str | None = None
    config_schema: dict[str, Any] | None = None

__all__ = [
    "PluginMetadata",
]
