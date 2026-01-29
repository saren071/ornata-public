"""Version management and compatibility checking for Ornata components.

This module provides semantic version parsing, comparison, and compatibility
checking for Ornata components and subsystems.
"""

from __future__ import annotations

from typing import Any

from ornata.api.exports.definitions import ComponentVersion, VersionCompatibilityError, VersionConstraint
from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


class VersionManager:
    """Manages version parsing, comparison, and compatibility checking."""

    def __init__(self) -> None:
        """Initialize the version manager."""
        self._logger = logger

    def parse_version(self, version_str: str) -> ComponentVersion:
        """Parse a version string into a ComponentVersion.

        Parameters
        ----------
        version_str : str
            Version string to parse (e.g., "1.2.3", "2.0.0-alpha.1", "1.0.0+build.123").

        Returns
        -------
        ComponentVersion
            Parsed version object.

        Raises
        ------
        VersionCompatibilityError
            If the version string is invalid.
        """
        try:
            return ComponentVersion.parse(version_str)
        except ValueError as e:
            raise VersionCompatibilityError(f"Invalid version format '{version_str}': {e}") from e

    def compare_versions(self, version1: ComponentVersion | str, version2: ComponentVersion | str) -> int:
        """Compare two versions.

        Parameters
        ----------
        version1 : ComponentVersion or str
            First version to compare.
        version2 : ComponentVersion or str
            Second version to compare.

        Returns
        -------
        int
            -1 if version1 < version2
             0 if version1 == version2
             1 if version1 > version2
        """
        v1 = version1 if isinstance(version1, ComponentVersion) else self.parse_version(version1)
        v2 = version2 if isinstance(version2, ComponentVersion) else self.parse_version(version2)

        # Compare major, minor, patch
        for attr in ['major', 'minor', 'patch']:
            diff = getattr(v1, attr) - getattr(v2, attr)
            if diff != 0:
                return 1 if diff > 0 else -1

        # Compare prerelease (prerelease versions are lower than release versions)
        if v1.prerelease and not v2.prerelease:
            return -1
        elif not v1.prerelease and v2.prerelease:
            return 1
        elif v1.prerelease and v2.prerelease:
            # Simple string comparison for prerelease identifiers
            if v1.prerelease < v2.prerelease:
                return -1
            elif v1.prerelease > v2.prerelease:
                return 1

        # Build metadata doesn't affect version precedence
        return 0

    def is_version_compatible(self, component_name: str, actual_version: ComponentVersion | str,
                            constraint: VersionConstraint) -> bool:
        """Check if a component version satisfies a version constraint.

        Parameters
        ----------
        component_name : str
            Name of the component for error reporting.
        actual_version : ComponentVersion or str
            The actual version of the component.
        constraint : VersionConstraint
            The version constraint to check against.

        Returns
        -------
        bool
            True if the version satisfies the constraint.

        Raises
        ------
        VersionCompatibilityError
            If version compatibility cannot be determined.
        """
        version = actual_version if isinstance(actual_version, ComponentVersion) else self.parse_version(actual_version)

        try:
            return constraint.is_satisfied_by(version)
        except Exception as e:
            raise VersionCompatibilityError(
                f"Failed to check version compatibility for {component_name}: {e}"
            ) from e

    def check_component_compatibility(self, component_name: str, required_version: str | None,
                                    actual_version: str | None) -> None:
        """Check if a component's actual version meets the required version.

        Parameters
        ----------
        component_name : str
            Name of the component.
        required_version : str or None
            Required version constraint (e.g., ">=1.0.0", "1.2.3").
        actual_version : str or None
            Actual version of the component.

        Raises
        ------
        VersionCompatibilityError
            If the component version is incompatible.
        """
        if not required_version or not actual_version:
            # No version requirement or no actual version - assume compatible
            return

        try:
            constraint = self._parse_constraint_string(required_version)
            actual = self.parse_version(actual_version)

            if not self.is_version_compatible(component_name, actual, constraint):
                raise VersionCompatibilityError(
                    f"Component '{component_name}' version {actual_version} does not satisfy requirement {required_version}",
                )
        except VersionCompatibilityError:
            raise
        except Exception as e:
            raise VersionCompatibilityError(
                f"Failed to check component version compatibility for {component_name}: {e}",
            ) from e

    def _parse_constraint_string(self, constraint_str: str) -> VersionConstraint:
        """Parse a version constraint string into a VersionConstraint object.

        Parameters
        ----------
        constraint_str : str
            Constraint string (e.g., ">=1.0.0", "1.2.3", "^2.0.0").

        Returns
        -------
        VersionConstraint
            Parsed version constraint.

        Raises
        ------
        VersionCompatibilityError
            If the constraint string is invalid.
        """
        constraint_str = constraint_str.strip()

        # Exact version
        if not any(op in constraint_str for op in ['>=', '<=', '>', '<', '^', '~']):
            try:
                exact_version = self.parse_version(constraint_str)
                return VersionConstraint(exact_version=exact_version)
            except Exception as e:
                raise VersionCompatibilityError(f"Invalid version constraint '{constraint_str}': {e}") from e

        # Handle common operators
        if constraint_str.startswith('>='):
            min_version = self.parse_version(constraint_str[2:].strip())
            return VersionConstraint(minimum_version=min_version)
        elif constraint_str.startswith('<='):
            max_version = self.parse_version(constraint_str[2:].strip())
            return VersionConstraint(maximum_version=max_version)
        elif constraint_str.startswith('>'):
            min_version = self.parse_version(constraint_str[1:].strip())
            # >1.0.0 is equivalent to >=1.0.1 for semantic versioning
            min_version = ComponentVersion(
                major=min_version.major,
                minor=min_version.minor,
                patch=min_version.patch + 1,
                prerelease=None,
                build=None
            )
            return VersionConstraint(minimum_version=min_version)
        elif constraint_str.startswith('<'):
            max_version = self.parse_version(constraint_str[1:].strip())
            return VersionConstraint(maximum_version=max_version)

        # Handle caret (^) and tilde (~) ranges
        elif constraint_str.startswith('^'):
            base_version = self.parse_version(constraint_str[1:].strip())
            if base_version.major > 0:
                max_version = ComponentVersion(
                    major=base_version.major + 1,
                    minor=0,
                    patch=0,
                    prerelease=None,
                    build=None
                )
            else:
                max_version = ComponentVersion(
                    major=0,
                    minor=base_version.minor + 1,
                    patch=0,
                    prerelease=None,
                    build=None
                )
            return VersionConstraint(minimum_version=base_version, maximum_version=max_version)

        elif constraint_str.startswith('~'):
            base_version = self.parse_version(constraint_str[1:].strip())
            max_version = ComponentVersion(
                major=base_version.major,
                minor=base_version.minor + 1,
                patch=0,
                prerelease=None,
                build=None
            )
            return VersionConstraint(minimum_version=base_version, maximum_version=max_version)

        else:
            raise VersionCompatibilityError(f"Unsupported version constraint operator in '{constraint_str}'")

    def get_version_info(self) -> dict[str, Any]:
        """Get version information about the Ornata system.

        Returns
        -------
        dict[str, Any]
            Dictionary containing version information.
        """
        try:
            import ornata
            version = getattr(ornata, '__version__', 'unknown')
        except Exception:
            version = 'unknown'

        return {
            'ornata_version': version,
            'python_version': f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}.{__import__('sys').version_info.micro}",
            'platform': __import__('platform').platform(),
        }


# Global version manager instance
_version_manager = VersionManager()


def check_component_version(component_name: str, required_version: str | None, actual_version: str | None) -> None:
    """Convenience function to check component version compatibility.

    Parameters
    ----------
    component_name : str
        Name of the component.
    required_version : str or None
        Required version constraint.
    actual_version : str or None
        Actual version of the component.

    Raises
    ------
    VersionCompatibilityError
        If the component version is incompatible.
    """
    _version_manager.check_component_compatibility(component_name, required_version, actual_version)


def parse_version(version_str: str) -> ComponentVersion:
    """Convenience function to parse a version string.

    Parameters
    ----------
    version_str : str
        Version string to parse.

    Returns
    -------
    ComponentVersion
        Parsed version object.
    """
    return _version_manager.parse_version(version_str)


def compare_versions(version1: ComponentVersion | str, version2: ComponentVersion | str) -> int:
    """Convenience function to compare two versions.

    Parameters
    ----------
    version1 : ComponentVersion or str
        First version to compare.
    version2 : ComponentVersion or str
        Second version to compare.

    Returns
    -------
    int
        Comparison result (-1, 0, or 1).
    """
    return _version_manager.compare_versions(version1, version2)


__all__ = [
    "VersionManager",
    "check_component_version",
    "parse_version",
    "compare_versions",
]
