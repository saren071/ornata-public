"""Ornata kernel bootstrap system.

This module implements the complete startup sequence for the Ornata system,
including configuration loading, backend selection, subsystem initialization,
event system setup, theme activation, and plugin discovery.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import BackendCapabilities, BackendSelectionError, BackendTarget, EventSystemInitError, KernelConfig, KernelInitError, KernelState, PluginLoadError, PluginMetadata, ThemeLoadError
from ornata.api.exports.utils import get_logger
from ornata.kernel.config import load_kernel_config
from ornata.kernel.registry import get_registry, register_subsystem
from ornata.kernel.versioning import check_component_version

if TYPE_CHECKING:
    from pathlib import Path

logger = get_logger(__name__)


class BootstrapPhase:
    """Base class for bootstrap phases."""

    def get_name(self) -> str:
        """Return the name of this bootstrap phase."""
        return self.__class__.__name__.replace('Phase', '').lower()

    def get_dependencies(self) -> set[str]:
        """Return the names of phases this phase depends on."""
        return set()

    def execute(self, state: KernelState) -> KernelState:
        """Execute this bootstrap phase and return updated state."""
        raise NotImplementedError("Subclasses must implement execute()")


class ConfigPhase(BootstrapPhase):
    """Phase for loading kernel configuration."""

    def execute(self, state: KernelState) -> KernelState:
        """Load kernel configuration."""
        try:
            config = load_kernel_config(state.config.config_search_paths if state.config else None)
            logger.info(f"Loaded kernel configuration: backend={config.primary_backend.value}")
            return KernelState(
                phase=state.phase,
                config=config,
                registered_subsystems=state.registered_subsystems,
                loaded_plugins=state.loaded_plugins,
                available_backends=state.available_backends,
                selected_backend=state.selected_backend,
                active_theme=state.active_theme,
                initialization_errors=state.initialization_errors
            )
        except Exception as e:
            raise KernelInitError(f"Configuration loading failed: {e}") from e


class BackendDiscoveryPhase(BootstrapPhase):
    """Phase for discovering available backends."""

    def get_dependencies(self) -> set[str]:
        return {"config"}

    def execute(self, state: KernelState) -> KernelState:
        """Discover available rendering backends."""
        if not state.config:
            raise KernelInitError("Configuration not loaded")

        backends: dict[BackendTarget, BackendCapabilities] = {}

        # Discover CLI backend (always available)
        backends[BackendTarget.CLI] = BackendCapabilities(
            backend_target=BackendTarget.CLI,
            name="CLI Renderer",
            version="1.0.0",
            available=True,
            supports_unicode=True,
            supports_colors=True,
            supports_mouse=False,
            supports_keyboard=True,
        )

        # Discover TTY backend
        try:
            backends[BackendTarget.TTY] = BackendCapabilities(
                backend_target=BackendTarget.TTY,
                name="TTY Renderer",
                version="1.0.0",
                available=True,
                supports_unicode=True,
                supports_colors=True,
                supports_mouse=False,
                supports_keyboard=True,
            )
        except ImportError:
            logger.debug("TTY backend not available")

        # Discover GUI backend
        if state.config.enable_gpu:
            try:
                gpu_info = BackendCapabilities(
                    backend_target=BackendTarget.GUI,
                    name="GPU Renderer",
                    version="1.0.0",
                    available=True,
                    supports_gpu=True,
                    supports_animations=True,
                    supports_unicode=True,
                    supports_colors=True,
                    supports_mouse=True,
                    supports_keyboard=True,
                    memory_usage_mb=1024
                )
                backends[BackendTarget.GUI] = BackendCapabilities(
                    backend_target=BackendTarget.GUI,
                    name=gpu_info.name,
                    version=gpu_info.version,
                    available=gpu_info.available,
                    supports_gpu=True,
                    supports_animations=True,
                    supports_unicode=True,
                    supports_colors=True,
                    supports_mouse=True,
                    supports_keyboard=True,
                    memory_usage_mb=gpu_info.memory_usage_mb,
                )
            except ImportError:
                logger.debug("GUI backend not available")

        logger.info(f"Discovered {len(backends)} backends: {[b.value for b in backends.keys()]}")
        return replace(state, available_backends=backends)


class BackendSelectionPhase(BootstrapPhase):
    """Phase for selecting the primary backend."""

    def get_dependencies(self) -> set[str]:
        return {"config", "backend_discovery"}

    def execute(self, state: KernelState) -> KernelState:
        """Select the primary backend based on configuration and availability."""
        if not state.config:
            raise KernelInitError("Configuration not loaded")

        primary_backend = state.config.primary_backend

        # Check if primary backend is available
        if primary_backend not in state.available_backends:
            # Try fallback backends
            for fallback in state.config.fallback_backends:
                if fallback in state.available_backends:
                    logger.warning(f"Primary backend {primary_backend.value} not available, using {fallback.value}")
                    selected_backend = fallback
                    break
            else:
                available = [b.value for b in state.available_backends.keys()]
                raise BackendSelectionError(
                    f"No suitable backend available. Requested: {primary_backend.value}, Available: {available}"
                )
        else:
            selected_backend = primary_backend

        logger.info(f"Selected backend: {selected_backend.value}")
        return replace(state, selected_backend=selected_backend)


class SubsystemRegistrationPhase(BootstrapPhase):
    """Phase for registering core subsystems."""

    def get_dependencies(self) -> set[str]:
        return {"config"}

    def execute(self, state: KernelState) -> KernelState:
        """Register core subsystems with the registry."""
        # Register core subsystems
        register_subsystem("layout", "1.0.0", dependencies=set())
        register_subsystem("rendering", "1.0.0", dependencies={"layout"})
        register_subsystem("events", "1.0.0", dependencies=set())
        register_subsystem("theme", "1.0.0", dependencies=set())
        register_subsystem("gpu", "1.0.0", dependencies=set())
        register_subsystem("plugins", "1.0.0", dependencies=set())

        logger.info("Registered core subsystems")
        return state


class EventSystemInitPhase(BootstrapPhase):
    """Phase for initializing the event system."""

    def get_dependencies(self) -> set[str]:
        return {"subsystem_registration"}

    def execute(self, state: KernelState) -> KernelState:
        """Initialize the event system."""
        try:
            from ornata.api.exports.events import EventSubsystem

            event_system = EventSubsystem()
            event_system.initialize()

            # Register event subsystem
            registry = get_registry()
            registry.update_subsystem_status("events", "ready")

            logger.info("Initialized event system")
            return state
        except Exception as e:
            raise EventSystemInitError(f"Event system initialization failed: {e}") from e


class ThemeActivationPhase(BootstrapPhase):
    """Phase for activating the theme system."""

    def get_dependencies(self) -> set[str]:
        return {"config", "subsystem_registration"}

    def execute(self, state: KernelState) -> KernelState:
        """Activate the theme system with the configured theme."""
        if not state.config:
            raise KernelInitError("Configuration not loaded")

        try:
            from ornata.api.exports.styling import get_theme_manager

            theme_manager = get_theme_manager()
            theme_manager.load_theme(state.config.default_theme)

            # Register theme subsystem as ready
            registry = get_registry()
            registry.update_subsystem_status("theme", "ready")

            logger.info(f"Activated theme: {state.config.default_theme}")
            return replace(state, active_theme=state.config.default_theme)
        except Exception as e:
            raise ThemeLoadError(f"Theme activation failed: {e}") from e


class PluginDiscoveryPhase(BootstrapPhase):
    """Phase for discovering and loading plugins."""

    def get_dependencies(self) -> set[str]:
        return {"config", "subsystem_registration"}

    def execute(self, state: KernelState) -> KernelState:
        """Discover and load plugins."""
        if not state.config:
            raise KernelInitError("Configuration not loaded")

        plugins: dict[str, PluginMetadata] = {}

        # Search for plugins in configured paths
        for search_path in state.config.plugin_search_paths:
            try:
                discovered = self._discover_plugins_in_path(search_path, state.config)
                plugins.update(discovered)
            except Exception as e:
                logger.warning(f"Plugin discovery failed in {search_path}: {e}")

        # Load enabled plugins
        loaded_plugins: dict[str, PluginMetadata] = {}
        for name, metadata in plugins.items():
            if name in state.config.disabled_plugins:
                logger.debug(f"Skipping disabled plugin: {name}")
                continue

            try:
                # Check version compatibility
                check_component_version(name, metadata.requires_ornata, self._get_ornata_version())

                # Load the plugin
                self._load_plugin(metadata)
                loaded_plugins[name] = metadata

                logger.info(f"Loaded plugin: {name} v{metadata.version}")
            except Exception as e:
                logger.warning(f"Failed to load plugin {name}: {e}")

        # Register plugins subsystem as ready
        registry = get_registry()
        registry.update_subsystem_status("plugins", "ready")

        logger.info(f"Loaded {len(loaded_plugins)} plugins")
        return replace(state, loaded_plugins=loaded_plugins)

    def _discover_plugins_in_path(self, search_path: str, config: KernelConfig) -> dict[str, PluginMetadata]:
        """Discover plugins in a specific search path."""
        from pathlib import Path

        plugins: dict[str, PluginMetadata] = {}

        try:
            path = Path(search_path)
            if not path.exists():
                return plugins

            # Look for plugin directories or files
            for item in path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # Check if it's a plugin directory
                    metadata = self._load_plugin_metadata(item)
                    if metadata:
                        plugins[metadata.name] = metadata
                elif item.suffix == '.py' and item.name != '__init__.py':
                    # Check if it's a plugin file
                    metadata = self._load_plugin_metadata_from_file(item)
                    if metadata:
                        plugins[metadata.name] = metadata

        except Exception as e:
            logger.debug(f"Error discovering plugins in {search_path}: {e}")

        return plugins

    def _load_plugin_metadata(self, plugin_dir: Path) -> PluginMetadata | None:
        """Load plugin metadata from a plugin directory."""
        metadata_file = plugin_dir / "plugin.json"
        if not metadata_file.exists():
            return None

        try:
            import json
            with open(metadata_file, encoding='utf-8') as f:
                data = json.load(f)

            return PluginMetadata(
                name=data['name'],
                version=data['version'],
                description=data.get('description'),
                author=data.get('author'),
                license=data.get('license'),
                provides_components=data.get('provides_components', []),
                provides_themes=data.get('provides_themes', []),
                provides_backends=data.get('provides_backends', []),
                provides_layouts=data.get('provides_layouts', []),
                requires_python=data.get('requires_python'),
                requires_ornata=data.get('requires_ornata'),
                requires_platforms=set(data.get('requires_platforms', [])),
                entry_point=data.get('entry_point'),
                config_schema=data.get('config_schema'),
            )
        except Exception as e:
            logger.debug(f"Failed to load plugin metadata from {metadata_file}: {e}")
            return None

    def _load_plugin_metadata_from_file(self, plugin_file: Path) -> PluginMetadata | None:
        """Load plugin metadata from a Python file."""
        # For now, skip file-based plugins - they need special handling
        return None

    def _load_plugin(self, metadata: PluginMetadata) -> Any:
        """Load a plugin based on its metadata."""
        if not metadata.entry_point:
            raise PluginLoadError(f"No entry point defined for plugin {metadata.name}")

        try:
            # Import the plugin module
            module_parts = metadata.entry_point.split('.')
            module_name = '.'.join(module_parts[:-1])
            class_name = module_parts[-1]

            module = __import__(module_name, fromlist=[class_name])
            plugin_class = getattr(module, class_name)

            # Instantiate the plugin
            return plugin_class()
        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin {metadata.name}: {e}") from e

    def _get_ornata_version(self) -> str | None:
        """Get the current Ornata version."""
        try:
            import ornata
            return getattr(ornata, '__version__', None)
        except Exception:
            return None


class KernelBootstrapper:
    """Main bootstrapper for the Ornata kernel."""

    def __init__(self) -> None:
        """Initialize the bootstrapper."""
        self._phases = self._create_phases()
        self._logger = logger

    def _create_phases(self) -> list[BootstrapPhase]:
        """Create the bootstrap phases in dependency order."""
        phases: list[BootstrapPhase] = [
            ConfigPhase(),
            BackendDiscoveryPhase(),
            BackendSelectionPhase(),
            SubsystemRegistrationPhase(),
            EventSystemInitPhase(),
            ThemeActivationPhase(),
            PluginDiscoveryPhase(),
        ]

        # Sort phases by dependencies
        return self._topological_sort(phases)

    def _topological_sort(self, phases: list[BootstrapPhase]) -> list[BootstrapPhase]:
        """Sort phases in topological order based on dependencies."""
        # Simple topological sort
        phase_dict: dict[str, BootstrapPhase] = {phase.get_name(): phase for phase in phases}
        visited: set[str] = set()
        visiting: set[str] = set()
        result: list[BootstrapPhase] = []

        def visit(phase: BootstrapPhase):
            name = phase.get_name()
            if name in visiting:
                raise KernelInitError(f"Circular dependency in bootstrap phases involving {name}")
            if name in visited:
                return

            visiting.add(name)
            for dep_name in phase.get_dependencies():
                if dep_name in phase_dict:
                    visit(phase_dict[dep_name])
            visiting.remove(name)
            visited.add(name)
            result.append(phase)

        for phase in phases:
            if phase.get_name() not in visited:
                visit(phase)

        return result

    def bootstrap(self) -> KernelState:
        """Execute the complete bootstrap sequence.

        Returns
        -------
        KernelState
            The final kernel state after bootstrap completion.

        Raises
        ------
        KernelInitError
            If bootstrap fails at any phase.
        """
        state: KernelState = KernelState(phase="uninitialized")
        errors: list[str] = []

        self._logger.info("Starting Ornata kernel bootstrap")

        for phase in self._phases:
            try:
                self._logger.debug(f"Executing bootstrap phase: {phase.get_name()}")
                state = replace(state, phase=f"bootstrapping_{phase.get_name()}")
                state = phase.execute(state)
            except Exception as e:
                error_msg = f"Bootstrap phase '{phase.get_name()}' failed: {e}"
                self._logger.error(error_msg)
                errors.append(error_msg)

                # Continue with other phases unless it's a critical failure
                if isinstance(e, (KernelInitError, BackendSelectionError)):
                    break

        # Update final state
        if errors:
            final_phase = "failed"
            state = replace(state, phase=final_phase, initialization_errors=errors)
            self._logger.error(f"Kernel bootstrap completed with {len(errors)} errors")
        else:
            final_phase = "ready"
            state = replace(state, phase=final_phase)
            self._logger.info("Kernel bootstrap completed successfully")

        return state


# Global bootstrapper instance
_bootstrapper = KernelBootstrapper()


def bootstrap_kernel() -> KernelState:
    """Bootstrap the Ornata kernel.

    Returns
    -------
    KernelState
        The final kernel state after bootstrap.
    """
    return _bootstrapper.bootstrap()


__all__ = [
    "KernelBootstrapper",
    "bootstrap_kernel",
]
