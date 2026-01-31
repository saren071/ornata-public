"""Central styling integration service for Ornata.

This service provides a unified interface for styling operations across all renderers,
connecting them to the theme system and ensuring consistent styling throughout the application.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger
from ornata.definitions.dataclasses.styling import StylingContext
from ornata.definitions.enums import BackendTarget
from ornata.styling.runtime.runtime import resolve_backend_component_style, resolve_component_style
from ornata.styling.theming.manager import ThemeManager

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.definitions.dataclasses.styling import BackendStylePayload, ResolvedStyle

logger = get_logger(__name__)


class StylingIntegrationService:
    """Central service for styling integration across all renderers.
    
    This service provides:
    1. Unified style resolution interface
    2. Theme system integration
    3. OSTS (Ornata Styling & Theming Sheet) resolution 
    4. Consistent styling across all renderers
    5. Removal of hardcoded defaults
    """
    
    def __init__(self, theme_manager: ThemeManager | None = None) -> None:
        """Initialize the styling integration service.
        
        Parameters
        ----------
        theme_manager : ThemeManager | None
            Theme manager instance. If None, creates a new one.
        """
        self._lock = threading.RLock()
        self._theme_manager = theme_manager or ThemeManager()
        self._renderer_cache: dict[str, dict[str, Any]] = {}
        self._capability_registry: dict[str, Callable[[], dict[str, Any]]] = {}
        self._cache_version = 0
        
        # Register default theme invalidator
        self._theme_manager.register_cache_invalidator(self._invalidate_caches)
        
        logger.debug("Styling integration service initialized")
    
    def get_renderer_capabilities(self, renderer_type: str) -> dict[str, Any]:
        """Get capabilities for a specific renderer type.
        
        Parameters
        ----------
        renderer_type : str
            Renderer type identifier.
            
        Returns
        -------
        dict[str, Any]
            Renderer capabilities.
        """
        with self._lock:
            if renderer_type in self._capability_registry:
                return self._capability_registry[renderer_type]()
            return self._get_default_capabilities(renderer_type)
    
    def register_renderer_capabilities(self, renderer_type: str, capabilities_func: Callable[[], dict[str, Any]]) -> None:
        """Register capabilities for a renderer type.
        
        Parameters
        ----------
        renderer_type : str
            Renderer type identifier.
        capabilities_func : Callable[[], dict[str, Any]]
            Function that returns renderer capabilities.
        """
        with self._lock:
            self._capability_registry[renderer_type] = capabilities_func
            self._invalidate_caches()
            logger.debug(f"Registered capabilities for renderer type: {renderer_type}")
    
    def resolve_style(
        self, 
        component_name: str, 
        state: dict[str, Any] | None = None,
        theme_overrides: dict[str, Any] | None = None,
        renderer_type: str | None = None,
        context_overrides: dict[str, Any] | None = None
    ) -> ResolvedStyle | None:
        """Resolve style for a component using the styling system.
        
        Parameters
        ----------
        component_name : str
            Component name to resolve style for.
        state : dict[str, Any] | None
            Component state for conditional styling.
        theme_overrides : dict[str, Any] | None
            Theme overrides for this component.
        renderer_type : str | None
            Target renderer type for capability-specific styling.
        context_overrides : dict[str, Any] | None
            Additional context overrides.
            
        Returns
        -------
        ResolvedStyle | None
            Resolved style or None if resolution fails.
        """
        if not state:
            state = {}
        if not theme_overrides:
            theme_overrides = {}
        if not context_overrides:
            context_overrides = {}
        
        try:
            # Get renderer capabilities
            if renderer_type:
                caps = self.get_renderer_capabilities(renderer_type)
            else:
                caps = self._get_default_capabilities("default")
            
            # Merge with context overrides
            caps.update(context_overrides)
            
            # Create styling context
            context = StylingContext(
                component_name=component_name,
                state=state,
                theme_overrides=theme_overrides,
                caps=caps
            )
            
            # Resolve the style
            return resolve_component_style(
                component_name=component_name,
                state=state,
                theme_overrides=theme_overrides,
                caps=context.caps
            )
        except Exception as e:
            logger.debug(f"Failed to resolve style for component '{component_name}': {e}")
            return None

    def resolve_backend_style(
        self,
        component_name: str,
        state: dict[str, Any] | None = None,
        theme_overrides: dict[str, Any] | None = None,
        renderer_type: str | None = None,
        backend: BackendTarget = BackendTarget.GUI,
        context_overrides: dict[str, Any] | None = None
    ) -> BackendStylePayload | None:
        """Resolve backend-conditioned style for a component.

        Parameters
        ----------
        component_name : str
            Component name to resolve style for.
        state : dict[str, Any] | None
            Component state for conditional styling.
        theme_overrides : dict[str, Any] | None
            Theme overrides for this component.
        renderer_type : str | None
            Target renderer type for capability-specific styling.
        backend : BackendTarget
            Target backend (GUI, CLI, TTY).
        context_overrides : dict[str, Any] | None
            Additional context overrides.

        Returns
        -------
        BackendStylePayload | None
            Backend-conditioned styling bundle or None if resolution fails.
        """
        if not state:
            state = {}
        if not theme_overrides:
            theme_overrides = {}
        if not context_overrides:
            context_overrides = {}

        try:
            # Get renderer capabilities
            if renderer_type:
                caps = self.get_renderer_capabilities(renderer_type)
            else:
                caps = self._get_default_capabilities(backend.value)

            # Merge with context overrides
            caps.update(context_overrides)

            # Resolve backend-conditioned style
            return resolve_backend_component_style(
                component_name=component_name,
                state=state,
                theme_overrides=theme_overrides,
                caps=caps,
                backend=backend,
            )
        except Exception as e:
            logger.debug(f"Failed to resolve backend style for component '{component_name}': {e}")
            return None

    def resolve_color_token(self, token: str) -> str | None:
        """Resolve a color token through the theme system.
        
        Parameters
        ----------
        token : str
            Color token to resolve.
            
        Returns
        -------
        str | None
            Resolved color value or None if not found.
        """
        return self._theme_manager.resolve_token(token)

    def resolve_theme_token(self, token: str) -> str | None:
        """Compatibility wrapper for resolving theme tokens (currently colours)."""
        return self.resolve_color_token(token)
    
    def get_active_theme_name(self) -> str | None:
        """Get the name of the currently active theme.
        
        Returns
        -------
        str | None
            Active theme name or None if no theme is active.
        """
        active_theme = self._theme_manager.get_active_theme()
        return active_theme.name if active_theme else None
    
    def set_theme(self, theme_name: str) -> None:
        """Set the active theme.
        
        Parameters
        ----------
        theme_name : str
            Name of the theme to activate.
        """
        self._theme_manager.set_active_theme(theme_name)
        logger.info(f"Theme changed to: {theme_name}")
    
    def list_themes(self) -> list[str]:
        """List all available themes.
        
        Returns
        -------
        list[str]
            List of theme names.
        """
        return self._theme_manager.list_themes()
    
    def load_theme_from_file(self, file_path: str, activate: bool = False) -> str:
        """Load a theme from file.
        
        Parameters
        ----------
        file_path : str
            Path to theme file.
        activate : bool
            Whether to activate the theme after loading.
            
        Returns
        -------
        str
            Name of the loaded theme.
        """
        theme = self._theme_manager.load_theme_file(file_path, activate=activate)
        return theme.name
    
    def load_theme_from_text(self, name: str, content: str, activate: bool = False) -> str:
        """Load a theme from text content.
        
        Parameters
        ----------
        name : str
            Theme name.
        content : str
            Theme content.
        activate : bool
            Whether to activate the theme after loading.
            
        Returns
        -------
        str
            Name of the loaded theme.
        """
        theme = self._theme_manager.load_theme_text(name, content, activate=activate)
        return theme.name
    
    def extend_theme(self, base_theme: str, overrides: dict[str, str], name: str | None = None) -> str:
        """Create a new theme based on an existing one with overrides.
        
        Parameters
        ----------
        base_theme : str
            Base theme name.
        overrides : dict[str, str]
            Theme overrides.
        name : str | None
            Name for the new theme. If None, generates one.
            
        Returns
        -------
        str
            Name of the new theme.
        """
        theme = self._theme_manager.extend_theme(base_theme, overrides, name=name)
        return theme.name
    
    def get_theme_info(self) -> dict[str, Any]:
        """Get information about the current theme system.
        
        Returns
        -------
        dict[str, Any]
            Theme system information.
        """
        with self._lock:
            return {
                "active_theme": self.get_active_theme_name(),
                "available_themes": self.list_themes(),
                "cache_version": self._cache_version,
                "registered_renderers": list(self._capability_registry.keys())
            }
    
    def _get_default_capabilities(self, renderer_type: str) -> dict[str, Any]:
        """Get default capabilities for a renderer type.
        
        Parameters
        ----------
        renderer_type : str
            Renderer type identifier.
            
        Returns
        -------
        dict[str, Any]
            Default capabilities.
        """
        default_caps = {
            "color_depth": "C256",
            "dpi": 96,
            "cell_metrics": lambda: (10, 16),
            "font_metrics": lambda: (12, 16)
        }
        
        # Renderer-specific defaults
        if renderer_type.lower() in ("cli", "tty"):
            default_caps["color_depth"] = "C16"
        elif renderer_type.lower() == "gui":
            default_caps["color_depth"] = "TRUECOLOR"
            default_caps["dpi"] = 96
            
        return default_caps
    
    def _invalidate_caches(self) -> None:
        """Invalidate all internal caches."""
        with self._lock:
            self._renderer_cache.clear()
            self._cache_version += 1
            logger.debug("Styling integration service caches invalidated")
    
    def __enter__(self) -> StylingIntegrationService:
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb: Any) -> None:
        """Context manager exit."""
        # Clean up resources if needed
        pass


# Global service instance
_global_service: StylingIntegrationService | None = None
_service_lock = threading.Lock()


def get_styling_service() -> StylingIntegrationService:
    """Get the global styling integration service instance.
    
    Returns
    -------
    StylingIntegrationService
        Global service instance.
    """
    global _global_service
    with _service_lock:
        if _global_service is None:
            _global_service = StylingIntegrationService()
        return _global_service


def reset_styling_service() -> None:
    """Reset the global styling service instance (for testing)."""
    global _global_service
    with _service_lock:
        _global_service = None

resolve_color = get_styling_service().resolve_color_token
