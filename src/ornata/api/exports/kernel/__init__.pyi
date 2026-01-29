"""Type stubs for the kernel subsystem exports."""

from __future__ import annotations

from ornata.kernel import bootstrap as bootstrap
from ornata.kernel import config as config
from ornata.kernel import versioning as versioning
from ornata.kernel.bootstrap import BackendDiscoveryPhase as BackendDiscoveryPhase
from ornata.kernel.bootstrap import BackendSelectionPhase as BackendSelectionPhase
from ornata.kernel.bootstrap import ConfigPhase as ConfigPhase
from ornata.kernel.bootstrap import EventSystemInitPhase as EventSystemInitPhase
from ornata.kernel.bootstrap import KernelBootstrapper as KernelBootstrapper
from ornata.kernel.bootstrap import PluginDiscoveryPhase as PluginDiscoveryPhase
from ornata.kernel.bootstrap import SubsystemRegistrationPhase as SubsystemRegistrationPhase
from ornata.kernel.bootstrap import ThemeActivationPhase as ThemeActivationPhase
from ornata.kernel.bootstrap import bootstrap_kernel as bootstrap_kernel  #type: ignore
from ornata.kernel.config import KernelConfigLoader as KernelConfigLoader
from ornata.kernel.config import load_kernel_config as load_kernel_config  #type: ignore
from ornata.kernel.registry import KernelSubsystemRegistry as KernelSubsystemRegistry
from ornata.kernel.registry import get_registry as get_registry
from ornata.kernel.registry import get_subsystem as get_subsystem  #type: ignore
from ornata.kernel.registry import register_subsystem as register_subsystem
from ornata.kernel.runtime import get_active_theme as get_active_theme
from ornata.kernel.runtime import get_initialization_errors as get_initialization_errors
from ornata.kernel.runtime import get_kernel_state as get_kernel_state  #type: ignore
from ornata.kernel.runtime import get_selected_backend as get_selected_backend  #type: ignore
from ornata.kernel.runtime import is_kernel_ready as is_kernel_ready
from ornata.kernel.versioning import VersionManager as VersionManager
from ornata.kernel.versioning import check_component_version as check_component_version
from ornata.kernel.versioning import compare_versions as compare_versions  #type: ignore
from ornata.kernel.versioning import parse_version as parse_version  #type: ignore

__all__ = [
    "BackendDiscoveryPhase",
    "BackendSelectionPhase",
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
    "versioning",
]