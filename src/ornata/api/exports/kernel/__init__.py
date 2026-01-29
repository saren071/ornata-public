"""Auto-generated lazy exports for the kernel subsystem."""

from __future__ import annotations

from importlib import import_module

from ornata.api._warnings import setup_internal_warnings

setup_internal_warnings()

_EXPORT_TARGETS: dict[str, str] = {
    "bootstrap": "ornata.kernel:bootstrap",
    "config": "ornata.kernel:config",
    "versioning": "ornata.kernel:versioning",
    "BackendDiscoveryPhase": "ornata.kernel.bootstrap:BackendDiscoveryPhase",
    "BackendSelectionPhase": "ornata.kernel.bootstrap:BackendSelectionPhase",
    "ConfigPhase": "ornata.kernel.bootstrap:ConfigPhase",
    "EventSystemInitPhase": "ornata.kernel.bootstrap:EventSystemInitPhase",
    "KernelBootstrapper": "ornata.kernel.bootstrap:KernelBootstrapper",
    "PluginDiscoveryPhase": "ornata.kernel.bootstrap:PluginDiscoveryPhase",
    "SubsystemRegistrationPhase": "ornata.kernel.bootstrap:SubsystemRegistrationPhase",
    "ThemeActivationPhase": "ornata.kernel.bootstrap:ThemeActivationPhase",
    "bootstrap_kernel": "ornata.kernel.bootstrap:bootstrap_kernel",
    "KernelConfigLoader": "ornata.kernel.config:KernelConfigLoader",
    "load_kernel_config": "ornata.kernel.config:load_kernel_config",
    "KernelSubsystemRegistry": "ornata.kernel.registry:KernelSubsystemRegistry",
    "get_registry": "ornata.kernel.registry:get_registry",
    "get_subsystem": "ornata.kernel.registry:get_subsystem",
    "register_subsystem": "ornata.kernel.registry:register_subsystem",
    "get_active_theme": "ornata.kernel.runtime:get_active_theme",
    "get_initialization_errors": "ornata.kernel.runtime:get_initialization_errors",
    "get_kernel_state": "ornata.kernel.runtime:get_kernel_state",
    "get_selected_backend": "ornata.kernel.runtime:get_selected_backend",
    "is_kernel_ready": "ornata.kernel.runtime:is_kernel_ready",
    "VersionManager": "ornata.kernel.versioning:VersionManager",
    "check_component_version": "ornata.kernel.versioning:check_component_version",
    "compare_versions": "ornata.kernel.versioning:compare_versions",
    "parse_version": "ornata.kernel.versioning:parse_version"
}

_RESOLVED_EXPORTS: dict[str, object] = {}

__all__ = ["__getattr__"]

def _load_target(name: str) -> object:
    """Load and cache ``name`` for this subsystem.

    Parameters
    ----------
    name : str
        Export name to resolve.

    Returns
    -------
    object
        Resolved attribute from the owning module.

    Raises
    ------
    AttributeError
        If ``name`` is unknown to this subsystem.
    """

    target = _EXPORT_TARGETS.get(name)
    if target is None:
        raise AttributeError(
            "module 'ornata.api.exports.kernel' has no attribute {name!r}"
        )
    module_name, _, attr_name = target.partition(':')
    module = import_module(module_name)
    value = getattr(module, attr_name)
    _RESOLVED_EXPORTS[name] = value
    globals()[name] = value
    return value

def __getattr__(name: str) -> object:
    """Resolve an export attribute on first access.

    Parameters
    ----------
    name : str
        Export name requested from this module.

    Returns
    -------
    object
        Resolved export value.

    Raises
    ------
    AttributeError
        If ``name`` is not part of this subsystem.
    """

    if name in _RESOLVED_EXPORTS:
        return _RESOLVED_EXPORTS[name]
    return _load_target(name)

def __dir__() -> list[str]:
    """Return the sorted list of exportable names.

    Returns
    -------
    list[str]
        Sorted names available via this module.
    """

    names = ['__getattr__']
    names.extend(_EXPORT_TARGETS)
    return sorted(names)
