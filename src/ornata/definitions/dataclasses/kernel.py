""" Kernel Dataclasses for Ornata """

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ornata.definitions.enums import BackendTarget, LogLevel

if TYPE_CHECKING:
    from ornata.definitions.dataclasses.plugins import PluginMetadata
    from ornata.definitions.dataclasses.rendering import BackendCapabilities


@dataclass(frozen=True)
class KernelConfig:
    """Complete kernel configuration loaded from files and environment."""
    primary_backend: BackendTarget = BackendTarget.CLI
    fallback_backends: list[BackendTarget] = field(default_factory=lambda: [BackendTarget.TTY])
    default_width: int | None = None
    default_height: int | None = None
    default_theme: str = "default"
    enable_gpu: bool = True
    enable_animations: bool = True
    log_level: LogLevel = LogLevel.INFO
    log_file: str | None = None
    enable_console_logging: bool = True
    plugin_paths: list[str] = field(default_factory=list)
    disabled_plugins: set[str] = field(default_factory=set)
    max_cache_size: int = 1000
    enable_threading: bool = True
    worker_threads: int = 4
    config_search_paths: list[str] = field(default_factory=lambda: ["."])
    theme_search_paths: list[str] = field(default_factory=lambda: ["themes"])
    plugin_search_paths: list[str] = field(default_factory=lambda: ["plugins"])
    env_overrides: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class KernelState:
    """Current state of the kernel bootstrap process."""
    phase: str
    config: KernelConfig | None = None
    registered_subsystems: dict[str, SubsystemInfo] = field(default_factory=dict)
    loaded_plugins: dict[str, PluginMetadata] = field(default_factory=dict)
    available_backends: dict[BackendTarget, BackendCapabilities] = field(default_factory=dict)
    selected_backend: BackendTarget | None = None
    active_theme: str | None = None
    initialization_errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SubsystemInfo:
    """Information about a registered subsystem."""
    name: str
    version: str
    status: str = "uninitialized"  # "uninitialized", "initializing", "ready", "failed"
    dependencies: set[str] = field(default_factory=set)
    capabilities: dict[str, Any] = field(default_factory=dict)

__all__ = [
    "KernelConfig",
    "KernelState",
    "SubsystemInfo",
]
