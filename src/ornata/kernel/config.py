"""Kernel configuration management for Ornata.

This module provides configuration loading and parsing for backend selection,
logging options, theme overrides, and plugin locations. It supports multiple
configuration sources including files and environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ornata.api.exports.definitions import BackendTarget, ConfigurationError, KernelConfig, LogLevel
from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


class KernelConfigLoader:
    """Loads and merges kernel configuration from multiple sources."""

    def __init__(self) -> None:
        """Initialize the configuration loader."""
        self._logger = logger

    def load_config(self, search_paths: list[str] | None = None) -> KernelConfig:
        """Load kernel configuration from files and environment variables.

        Parameters
        ----------
        search_paths : list[str], optional
            Paths to search for configuration files. Defaults to current directory.

        Returns
        -------
        KernelConfig
            The loaded and merged kernel configuration.

        Raises
        ------
        ConfigurationError
            If configuration loading or parsing fails.
        """
        search_paths = search_paths or ["."]

        # Load configuration from files
        file_config = self._load_from_files(search_paths)

        # Load configuration from environment variables
        env_config = self._load_from_environment()

        # Merge configurations (environment overrides files)
        merged_config = self._merge_configs(file_config, env_config)

        # Validate and create KernelConfig
        try:
            return self._create_kernel_config(merged_config)
        except Exception as e:
            raise ConfigurationError(f"Failed to create kernel config: {e}") from e

    def _load_from_files(self, search_paths: list[str]) -> dict[str, Any]:
        """Load configuration from files in search paths.

        Parameters
        ----------
        search_paths : list[str]
            Paths to search for configuration files.

        Returns
        -------
        dict[str, Any]
            Configuration loaded from files.
        """
        config: dict[str, Any] = {}

        # Configuration files to look for (in priority order)
        config_files = [
            "ornata.config",
            "or.config",
            ".ornata",
            "ornata.ini"
        ]

        for search_path in search_paths:
            path = Path(search_path)
            if not path.exists():
                continue

            for config_file in config_files:
                config_path = path / config_file
                if config_path.exists():
                    try:
                        file_config = self._parse_config_file(config_path)
                        config.update(file_config)
                        self._logger.debug(f"Loaded config from {config_path}")
                    except Exception as e:
                        self._logger.warning(f"Failed to parse config file {config_path}: {e}")

        return config

    def _parse_config_file(self, config_path: Path) -> dict[str, Any]:
        """Parse a configuration file.

        Parameters
        ----------
        config_path : Path
            Path to the configuration file.

        Returns
        -------
        dict[str, Any]
            Parsed configuration.

        Raises
        ------
        ConfigurationError
            If the file cannot be parsed.
        """
        try:
            content = config_path.read_text(encoding="utf-8")
        except Exception as e:
            raise ConfigurationError(f"Cannot read config file {config_path}: {e}") from e

        config: dict[str, Any] = {}

        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if "=" not in line:
                raise ConfigurationError(
                    f"Invalid config line {line_num}: expected 'key=value' format",
                )

            key, value = line.split("=", 1)
            key = key.strip().lower()
            value = value.strip()

            # Handle special value parsing
            if value.lower() in ("true", "yes", "1", "on"):
                value = True
            elif value.lower() in ("false", "no", "0", "off"):
                value = False
            elif value.isdigit():
                value = int(value)
            elif value.replace(".", "").isdigit() and value.count(".") == 1:
                value = float(value)

            config[key] = value

        return config

    def _load_from_environment(self) -> dict[str, Any]:
        """Load configuration from environment variables.

        Returns
        -------
        dict[str, Any]
            Configuration from environment variables.
        """
        config: dict[str, Any] = {}

        # Environment variable mappings
        env_mappings = {
            "ORNATA_BACKEND": "primary_backend",
            "ORNATA_THEME": "default_theme",
            "ORNATA_LOG_LEVEL": "log_level",
            "ORNATA_LOG_FILE": "log_file",
            "ORNATA_WIDTH": "default_width",
            "ORNATA_HEIGHT": "default_height",
            "ORNATA_GPU": "enable_gpu",
            "ORNATA_ANIMATIONS": "enable_animations",
            "ORNATA_THREADING": "enable_threading",
            "ORNATA_WORKER_THREADS": "worker_threads",
            "ORNATA_MAX_CACHE_SIZE": "max_cache_size",
            "ORNATA_PLUGIN_PATHS": "plugin_paths",
            "ORNATA_DISABLED_PLUGINS": "disabled_plugins",
        }

        for env_var, config_key in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Parse environment variable values
                if value.lower() in ("true", "yes", "1", "on"):
                    value = True
                elif value.lower() in ("false", "no", "0", "off"):
                    value = False
                elif value.isdigit():
                    value = int(value)
                elif config_key == "plugin_paths":
                    # Handle comma-separated paths
                    value = [path.strip() for path in value.split(",") if path.strip()]
                elif config_key == "disabled_plugins":
                    # Handle comma-separated plugin names
                    value = {name.strip() for name in value.split(",") if name.strip()}

                config[config_key] = value
                self._logger.debug(f"Loaded config from environment: {env_var}={value}")

        return config

    def _merge_configs(self, base_config: dict[str, Any], override_config: dict[str, Any]) -> dict[str, Any]:
        """Merge two configurations with override taking precedence.

        Parameters
        ----------
        base_config : dict[str, Any]
            Base configuration (from files).
        override_config : dict[str, Any]
            Override configuration (from environment).

        Returns
        -------
        dict[str, Any]
            Merged configuration.
        """
        merged = base_config.copy()
        merged.update(override_config)

        # Special handling for list/set merging
        for key in ["plugin_paths", "config_search_paths", "theme_search_paths", "plugin_search_paths"]:
            if key in base_config and key in override_config:
                # Environment overrides completely
                merged[key] = override_config[key]
            elif key in base_config:
                merged[key] = base_config[key]
            elif key in override_config:
                merged[key] = override_config[key]

        for key in ["disabled_plugins"]:
            if key in base_config and key in override_config:
                # Environment overrides completely
                merged[key] = override_config[key]
            elif key in base_config:
                merged[key] = base_config[key]
            elif key in override_config:
                merged[key] = override_config[key]

        return merged

    def _create_kernel_config(self, config: dict[str, Any]) -> KernelConfig:
        """Create a KernelConfig instance from parsed configuration.

        Parameters
        ----------
        config : dict[str, Any]
            Parsed configuration dictionary.

        Returns
        -------
        KernelConfig
            Validated kernel configuration.

        Raises
        ------
        ConfigurationError
            If configuration values are invalid.
        """
        # Parse backend type
        backend_str = config.get("primary_backend", "cli").lower()
        try:
            primary_backend = BackendTarget(backend_str)
        except ValueError as e:
            raise ConfigurationError(
                f"Invalid backend type: {backend_str}. Must be one of: {[b.value for b in BackendTarget]}",
            ) from e

        # Parse fallback backends
        fallback_strs = config.get("fallback_backends", ["tty"])
        if isinstance(fallback_strs, str):
            fallback_strs = [s.strip() for s in fallback_strs.split(",") if s.strip()]

        fallback_backends: list[BackendTarget] = []
        for backend_str in fallback_strs:
            try:
                fallback_backends.append(BackendTarget(backend_str.lower()))
            except ValueError:
                self._logger.warning(f"Ignoring invalid fallback backend: {backend_str}")

        # Parse log level
        log_level_str = config.get("log_level", "info").lower()
        try:
            log_level = LogLevel(log_level_str)
        except ValueError as e:
            raise ConfigurationError(
                f"Invalid log level: {log_level_str}. Must be one of: {[level.value for level in LogLevel]}",
            ) from e

        # Parse plugin paths
        plugin_paths = config.get("plugin_paths", [])
        if isinstance(plugin_paths, str):
            plugin_paths = [path.strip() for path in plugin_paths.split(",") if path.strip()]

        # Parse disabled plugins
        disabled_plugins: set[str] = config.get("disabled_plugins", set())
        if isinstance(disabled_plugins, str):
            disabled_plugins = {name.strip() for name in disabled_plugins.split(",") if name.strip()}

        return KernelConfig(
            primary_backend=primary_backend,
            fallback_backends=fallback_backends,
            default_width=config.get("default_width"),
            default_height=config.get("default_height"),
            default_theme=config.get("default_theme", "default"),
            enable_gpu=config.get("enable_gpu", True),
            enable_animations=config.get("enable_animations", True),
            log_level=log_level,
            log_file=config.get("log_file"),
            enable_console_logging=config.get("enable_console_logging", True),
            plugin_paths=plugin_paths,
            disabled_plugins=disabled_plugins,
            max_cache_size=config.get("max_cache_size", 1000),
            enable_threading=config.get("enable_threading", True),
            worker_threads=config.get("worker_threads", 4),
            config_search_paths=config.get("config_search_paths", ["."]),
            theme_search_paths=config.get("theme_search_paths", ["themes"]),
            plugin_search_paths=config.get("plugin_search_paths", ["plugins"]),
            env_overrides=config.get("env_overrides", {}),
        )


# Convenience function for loading configuration
def load_kernel_config(search_paths: list[str] | None = None) -> KernelConfig:
    """Load kernel configuration from files and environment variables.

    Parameters
    ----------
    search_paths : list[str], optional
        Paths to search for configuration files.

    Returns
    -------
    KernelConfig
        The loaded kernel configuration.
    """
    loader = KernelConfigLoader()
    return loader.load_config(search_paths)


__all__ = [
    "KernelConfigLoader",
    "load_kernel_config",
]
