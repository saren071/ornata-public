"""Subsystem registry for Ornata kernel.

This module provides registration and management of kernel subsystems including
layout engines, rendering backends, event systems, and other core components.
"""

from __future__ import annotations

from typing import Any

from ornata.api.exports.definitions import SubsystemInfo, SubsystemRegistrationError, SubsystemRegistry
from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


class KernelSubsystemRegistry(SubsystemRegistry):
    """Registry for managing kernel subsystems and their dependencies."""

    def __init__(self) -> None:
        """Initialize the subsystem registry."""
        self._subsystems: dict[str, SubsystemInfo] = {}
        self._logger = logger

    def register_subsystem(self, name: str, info: SubsystemInfo) -> None:
        """Register a subsystem with the registry.

        Parameters
        ----------
        name : str
            Unique name for the subsystem.
        info : SubsystemInfo
            Information about the subsystem.

        Raises
        ------
        SubsystemRegistrationError
            If registration fails or the subsystem is already registered.
        """
        if name in self._subsystems:
            raise SubsystemRegistrationError(f"Subsystem '{name}' is already registered")

        # Check if all dependencies are registered
        for dependency in info.dependencies:
            if dependency not in self._subsystems:
                raise SubsystemRegistrationError(
                    f"Cannot register subsystem '{name}': dependency '{dependency}' not found"
                )

        self._subsystems[name] = info
        self._logger.debug(f"Registered subsystem '{name}' with status '{info.status}'")

    def unregister_subsystem(self, name: str) -> None:
        """Unregister a subsystem from the registry.

        Parameters
        ----------
        name : str
            Name of the subsystem to unregister.

        Raises
        ------
        SubsystemRegistrationError
            If the subsystem is not registered or has dependents.
        """
        if name not in self._subsystems:
            raise SubsystemRegistrationError(f"Subsystem '{name}' is not registered")

        # Check if any other subsystems depend on this one
        dependents: list[str] = []
        for other_name, other_info in self._subsystems.items():
            if other_name != name and name in other_info.dependencies:
                dependents.append(other_name)

        if dependents:
            raise SubsystemRegistrationError(
                f"Cannot unregister subsystem '{name}': required by {dependents}",
            )

        del self._subsystems[name]
        self._logger.debug(f"Unregistered subsystem '{name}'")

    def get_subsystem(self, name: str) -> SubsystemInfo | None:
        """Get information about a registered subsystem.

        Parameters
        ----------
        name : str
            Name of the subsystem.

        Returns
        -------
        SubsystemInfo or None
            Information about the subsystem, or None if not registered.
        """
        return self._subsystems.get(name)

    def get_subsystems_by_status(self, status: str) -> list[SubsystemInfo]:
        """Get all subsystems with a specific status.

        Parameters
        ----------
        status : str
            Status to filter by.

        Returns
        -------
        list[SubsystemInfo]
            List of subsystems with the specified status.
        """
        return [info for info in self._subsystems.values() if info.status == status]

    def check_dependencies(self, subsystem_name: str) -> bool:
        """Check if all dependencies for a subsystem are satisfied.

        Parameters
        ----------
        subsystem_name : str
            Name of the subsystem to check.

        Returns
        -------
        bool
            True if all dependencies are satisfied, False otherwise.
        """
        info = self._subsystems.get(subsystem_name)
        if not info:
            return False

        for dependency in info.dependencies:
            dep_info = self._subsystems.get(dependency)
            if not dep_info or dep_info.status != "ready":
                return False

        return True

    def update_subsystem_status(self, name: str, status: str) -> None:
        """Update the status of a registered subsystem.

        Parameters
        ----------
        name : str
            Name of the subsystem.
        status : str
            New status for the subsystem.

        Raises
        ------
        SubsystemRegistrationError
            If the subsystem is not registered.
        """
        if name not in self._subsystems:
            raise SubsystemRegistrationError(f"Subsystem '{name}' is not registered")

        old_status = self._subsystems[name].status
        current = self._subsystems[name]
        self._subsystems[name] = SubsystemInfo(
            name=name,
            version=current.version,
            dependencies=current.dependencies,
            capabilities=current.capabilities,
            status=status
        )
        self._logger.debug(f"Updated subsystem '{name}' status: {old_status} -> {status}")

    def get_all_subsystems(self) -> dict[str, SubsystemInfo]:
        """Get all registered subsystems.

        Returns
        -------
        dict[str, SubsystemInfo]
            Dictionary mapping subsystem names to their information.
        """
        return self._subsystems.copy()

    def get_dependency_graph(self) -> dict[str, set[str]]:
        """Get the dependency graph for all subsystems.

        Returns
        -------
        dict[str, set[str]]
            Dictionary mapping subsystem names to their dependencies.
        """
        return {name: info.dependencies for name, info in self._subsystems.items()}

    def get_reverse_dependency_graph(self) -> dict[str, set[str]]:
        """Get the reverse dependency graph (what depends on what).

        Returns
        -------
        dict[str, set[str]]
            Dictionary mapping subsystem names to subsystems that depend on them.
        """
        reverse_deps: dict[str, set[str]] = {}

        for name in self._subsystems:
            reverse_deps[name] = set()

        for name, info in self._subsystems.items():
            for dep in info.dependencies:
                if dep in reverse_deps:
                    reverse_deps[dep].add(name)

        return reverse_deps

    def get_initialization_order(self) -> list[str]:
        """Get the order in which subsystems should be initialized based on dependencies.

        Returns
        -------
        list[str]
            List of subsystem names in initialization order.

        Raises
        ------
        SubsystemRegistrationError
            If there are circular dependencies.
        """
        # Simple topological sort
        visited: set[str] = set()
        visiting: set[str] = set()
        order: list[str] = []

        def visit(name: str) -> None:
            if name in visiting:
                raise SubsystemRegistrationError(f"Circular dependency detected involving '{name}'")
            if name in visited:
                return

            visiting.add(name)
            info = self._subsystems.get(name)
            if info:
                for dep in info.dependencies:
                    visit(dep)
            visiting.remove(name)
            visited.add(name)
            order.append(name)

        for name in self._subsystems:
            if name not in visited:
                visit(name)

        return order


# Global registry instance
_registry = KernelSubsystemRegistry()


def get_registry() -> KernelSubsystemRegistry:
    """Get the global subsystem registry instance.

    Returns
    -------
    KernelSubsystemRegistry
        The global registry instance.
    """
    return _registry


def register_subsystem(name: str, version: str, dependencies: set[str] | None = None, capabilities: dict[str, Any] | None = None) -> None:
    """Convenience function to register a subsystem.

    Parameters
    ----------
    name : str
        Unique name for the subsystem.
    version : str
        Version string for the subsystem.
    dependencies : set[str], optional
        Set of subsystem names this subsystem depends on.
    capabilities : dict[str, Any], optional
        Dictionary of capabilities provided by this subsystem.
    """
    info = SubsystemInfo(
        name=name,
        version=version,
        dependencies=dependencies or set(),
        capabilities=capabilities or {}
    )
    _registry.register_subsystem(name, info)


def get_subsystem(name: str) -> SubsystemInfo | None:
    """Convenience function to get a subsystem.

    Parameters
    ----------
    name : str
        Name of the subsystem.

    Returns
    -------
    SubsystemInfo or None
        Information about the subsystem, or None if not registered.
    """
    return _registry.get_subsystem(name)


__all__ = [
    "KernelSubsystemRegistry",
    "get_registry",
    "register_subsystem",
    "get_subsystem",
]
