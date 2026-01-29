"""Auto-generated exports for ornata.kernel."""

from __future__ import annotations

from . import bootstrap, config, registry, runtime, versioning
from .bootstrap import (
    BackendDiscoveryPhase,
    BackendSelectionPhase,
    BootstrapPhase,
    ConfigPhase,
    EventSystemInitPhase,
    KernelBootstrapper,
    PluginDiscoveryPhase,
    SubsystemRegistrationPhase,
    ThemeActivationPhase,
    bootstrap_kernel,
)
from .config import (
    KernelConfigLoader,
    load_kernel_config,
)
from .registry import (
    KernelSubsystemRegistry,
    get_registry,
    get_subsystem,
    register_subsystem,
)
from .runtime import (
    get_active_theme,
    get_initialization_errors,
    get_kernel_state,
    get_selected_backend,
    is_kernel_ready,
)
from .versioning import (
    VersionManager,
    check_component_version,
    compare_versions,
    parse_version,
)

__all__ = [
    "BackendDiscoveryPhase",
    "BackendSelectionPhase",
    "BootstrapPhase",
    "ConfigPhase",
    "EventSystemInitPhase",
    "KernelBootstrapper",
    "KernelConfigLoader",
    "KernelSubsystemRegistry",
    "PluginDiscoveryPhase",
    "SubsystemRegistrationPhase",
    "ThemeActivationPhase",
    "VersionManager",
    "bootstrap",
    "bootstrap_kernel",
    "check_component_version",
    "compare_versions",
    "config",
    "get_active_theme",
    "get_initialization_errors",
    "get_kernel_state",
    "get_registry",
    "get_selected_backend",
    "get_subsystem",
    "is_kernel_ready",
    "load_kernel_config",
    "parse_version",
    "register_subsystem",
    "registry",
    "runtime",
    "versioning",
]
