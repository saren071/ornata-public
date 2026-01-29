"""Ornata kernel system.

This module provides the kernel bootstrap and management functionality for Ornata.
The kernel handles system initialization, configuration, backend selection, and
subsystem coordination.
"""

from __future__ import annotations

from ornata.api.exports.definitions import (
    BackendCapabilities,
    BackendSelectionError,
    BackendSelector,
    BackendTarget,
    BootstrapPhase,
    ComponentVersion,
    ConfigLoader,
    ConfigurationError,
    EventSystemInitError,
    KernelConfig,
    KernelError,
    KernelInitError,
    KernelState,
    LogLevel,
    PluginLoader,
    PluginLoadError,
    PluginMetadata,
    SubsystemInfo,
    SubsystemRegistrationError,
    SubsystemRegistry,
    ThemeLoadError,
    VersionCompatibilityError,
    VersionConstraint,
)
from ornata.kernel.bootstrap import KernelBootstrapper, bootstrap_kernel
from ornata.kernel.config import KernelConfigLoader, load_kernel_config
from ornata.kernel.registry import KernelSubsystemRegistry, get_registry, get_subsystem, register_subsystem
from ornata.kernel.versioning import VersionManager, check_component_version, compare_versions, parse_version

# Bootstrap the kernel on import
_kernel_state = bootstrap_kernel()

# Make key components available
def get_kernel_state() -> KernelState:
    """Get the current kernel state.

    Returns
    -------
    KernelState
        The current state of the kernel after bootstrap.
    """
    return _kernel_state


def is_kernel_ready() -> bool:
    """Check if the kernel is fully initialized and ready.

    Returns
    -------
    bool
        True if the kernel is ready, False otherwise.
    """
    return _kernel_state.phase == "ready"


def get_selected_backend() -> BackendTarget | None:
    """Get the currently selected backend.

    Returns
    -------
    BackendTarget or None
        The selected backend, or None if none was selected.
    """
    return _kernel_state.selected_backend


def get_active_theme() -> str | None:
    """Get the currently active theme.

    Returns
    -------
    str or None
        The active theme name, or None if no theme is active.
    """
    return _kernel_state.active_theme


def get_initialization_errors() -> list[str]:
    """Get any errors that occurred during kernel initialization.

    Returns
    -------
    list[str]
        List of error messages from initialization.
    """
    return _kernel_state.initialization_errors.copy()


# Export public API
__all__ = [
    # Bootstrap functionality
    "KernelBootstrapper",
    "bootstrap_kernel",
    "get_kernel_state",
    "is_kernel_ready",
    "get_selected_backend",
    "get_active_theme",
    "get_initialization_errors",

    # Configuration
    "KernelConfigLoader",
    "load_kernel_config",

    # Registry
    "KernelSubsystemRegistry",
    "get_registry",
    "register_subsystem",
    "get_subsystem",

    # Versioning
    "VersionManager",
    "check_component_version",
    "compare_versions",
    "parse_version",

    # Types
    "BackendCapabilities",
    "BackendSelector",
    "BackendTarget",
    "BootstrapPhase",
    "ComponentVersion",
    "ConfigLoader",
    "KernelConfig",
    "KernelState",
    "LogLevel",
    "PluginLoader",
    "PluginMetadata",
    "SubsystemInfo",
    "SubsystemRegistry",
    "VersionConstraint",

    # Errors
    "BackendSelectionError",
    "ConfigurationError",
    "EventSystemInitError",
    "KernelError",
    "KernelInitError",
    "PluginLoadError",
    "SubsystemRegistrationError",
    "ThemeLoadError",
    "VersionCompatibilityError",
]
