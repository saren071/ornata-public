"""Public interface for the Ornata styling subsystem."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger
from ornata.definitions.enums import BackendTarget

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from ornata.api.exports.definitions import CacheKey, ColorBlend, ColorSpec, FontDef, Insets, Length, ResolvedStyle, StylingContext
    from ornata.definitions.dataclasses.layout import LayoutStyle
    from ornata.definitions.dataclasses.styling import BackendStylePayload
    from ornata.styling.language.engine import StyleEngine

class _ResolutionCounter:
    # local defined counter
    _resolution_counter = 0
    def increment(self):
        self._resolution_counter += 1

    def get(self):
        return self._resolution_counter
    
class StylingRuntime:
    """Facade around :class:`StyleEngine` providing caching, theming, and stats."""

    def __init__(self) -> None:
        """Create a styling subsystem instance."""
        from ornata.styling.language.engine import StyleEngine
        from ornata.styling.theming.manager import get_theme_manager
        self.logger = get_logger(__name__)
        self._engine = StyleEngine()
        self._theme_manager = get_theme_manager()
        self._cache: dict[CacheKey, ResolvedStyle] = {}
        self._font_registry: dict[str, FontDef] = {}
        self._font_registry_version = -1
        self._font_registry_lock = threading.RLock()
        self._resolution_counter = _ResolutionCounter()

        # Register for theme change notifications to invalidate caches
        self._theme_manager.register_cache_invalidator(self.invalidate_cache)

    def resolve_style(self, context: StylingContext) -> ResolvedStyle:
        """Resolve a style for ``context`` using cache acceleration.

        Args:
            context (StylingContext): Styling context describing the component.

        Returns:
            ResolvedStyle: Resolved style produced by the engine.
        """
        from ornata.api.exports.definitions import CacheKey

        overrides = context.theme_overrides or {}
        overrides_items = tuple(sorted((str(key), str(value)) for key, value in overrides.items()))
        caps_signature = _caps_signature(context.caps)
        key = CacheKey(
            component=context.component_name,
            states=context.active_states(),
            overrides=overrides_items,
            style_version=self._engine.theme_version,
            theme_version=self._theme_manager.version,
            caps_signature=caps_signature
        )

        cached = self._cache.get(key)
        if cached is not None:
            self.logger.debug("style cache hit for %s states=%s", key.component, sorted(key.states))
            return cached

        resolved = self._engine.resolve(
            node={"component_name": context.component_name},
            state=context.state or {},
            caps=context.caps,
            overrides=context.theme_overrides,
        )
        self._resolution_counter.increment()

        self._cache[key] = resolved
        return resolved

    def resolve_backend_style(self, context: StylingContext) -> BackendStylePayload:
        """Resolve a style and produce backend-conditioned payload.

        Args:
            context (StylingContext): Styling context with backend target.

        Returns:
            BackendStylePayload: Backend-conditioned styling bundle.
        """
        from ornata.definitions.dataclasses.styling import BackendStylePayload

        backend = context.backend
        resolved = self.resolve_style(context)

        # Filter/convert style based on backend capabilities
        filtered_style = self._filter_style_for_backend(resolved, backend)

        # Build renderer-specific metadata
        renderer_metadata = self._build_renderer_metadata(filtered_style, backend, context.caps)

        # Build layout style from filtered style
        layout_style = self._build_layout_style(filtered_style, backend)

        return BackendStylePayload(
            backend=backend,
            style=filtered_style,
            renderer_metadata=renderer_metadata,
            layout_style=layout_style,
            extras={},
        )

    def _filter_style_for_backend(self, style: ResolvedStyle, backend: BackendTarget) -> ResolvedStyle:
        """Filter and convert style fields based on backend capabilities.

        Args:
            style (ResolvedStyle): Original resolved style.
            backend (BackendTarget): Target backend.

        Returns:
            ResolvedStyle: Backend-filtered style.
        """
        from copy import copy

        filtered = copy(style)

        if backend in (BackendTarget.CLI, BackendTarget.TTY):
            # CLI backends need cell-based units, not px
            filtered = self._convert_lengths_to_cells(filtered)

            # Convert colors to ANSI strings for CLI/TTY backends
            try:
                from ornata.styling.colorkit.resolver import ColorResolver

                resolver = ColorResolver(
                    theme_lookup=self._theme_manager.resolve_token,
                    theme_version_provider=lambda: self._theme_manager.version,
                )
                if filtered.color is not None:
                    filtered.color = resolver.resolve_ansi(filtered.color)
                if getattr(filtered, "background", None) is not None:
                    bg_spec = filtered.background
                    filtered.background = (
                        resolver.resolve_background(bg_spec)
                        if isinstance(bg_spec, str)
                        else resolver.resolve_ansi(bg_spec)
                    )
            except Exception:
                pass

        return filtered

    def _convert_lengths_to_cells(self, style: ResolvedStyle) -> ResolvedStyle:
        """Convert px-based lengths to cell-based for CLI backends.

        Args:
            style (ResolvedStyle): Style with px lengths.

        Returns:
            ResolvedStyle: Style with cell-based lengths.
        """
        from copy import copy

        converted = copy(style)
        cell_fields = ["width", "height", "min_width", "min_height", "max_width", "max_height",
                       "top", "right", "bottom", "left", "font_size", "letter_spacing", "word_spacing"]

        for field_name in cell_fields:
            value = getattr(style, field_name)
            if value is not None and hasattr(value, "unit") and value.unit == "px":
                # Approximate px to cells (assuming 10px per cell width, 16px per cell height)
                cell_value = value.value / 10.0  # Simplified conversion
                setattr(converted, field_name, type(value)(cell_value, "cell"))

        return converted

    def _build_renderer_metadata(self, style: ResolvedStyle, backend: BackendTarget, caps: Any | None) -> dict[str, Any]:
        """Build renderer-specific metadata bundle.

        Args:
            style (ResolvedStyle): Filtered style.
            backend (BackendTarget): Target backend.
            caps (Any | None): Capability descriptor.

        Returns:
            dict[str, Any]: Renderer metadata.
        """
        metadata: dict[str, Any] = {
            "backend": backend.value,
        }

        # Add border thickness flag for CLI
        if backend in (BackendTarget.CLI, BackendTarget.TTY) and style.border:
            border_width = style.border.width if style.border else 0
            metadata["border_thick"] = border_width >= 2

        # Add color metadata based on backend color depth
        if caps:
            color_depth = getattr(caps, "color_depth", "C256") if not callable(getattr(caps, "color_depth", None)) else caps.color_depth()
            metadata["color_depth"] = color_depth

        return metadata

    def _build_layout_style(self, style: ResolvedStyle, backend: BackendTarget) -> LayoutStyle:
        """Build LayoutStyle from filtered ResolvedStyle.

        Args:
            style (ResolvedStyle): Filtered resolved style.
            backend (BackendTarget): Target backend.

        Returns:
            LayoutStyle: Layout-ready style.
        """
        from ornata.definitions.dataclasses.layout import LayoutStyle

        layout = LayoutStyle()

        # Copy layout-relevant fields
        layout_fields = [
            "width", "height", "min_width", "min_height", "max_width", "max_height",
            "padding", "margin", "display", "position",
            "flex_direction", "justify", "align",
            "flex_grow", "flex_shrink", "flex_basis", "wrap",
        ]

        for field_name in layout_fields:
            if hasattr(style, field_name):
                value = getattr(style, field_name)
                setattr(layout, field_name, value)
                # Sync direction when flex_direction is set
                if field_name == "flex_direction" and value is not None:
                    layout.direction = value

        return layout

    def invalidate_cache(self, component_name: str | None = None) -> None:
        """Invalidate cached styles.

        Args:
            component_name (str | None): When provided, only entries for the component are removed.

        Returns:
            None
        """
        if component_name is None:
            self._cache.clear()
            return
        to_remove = [key for key in self._cache if key.component == component_name]
        for key in to_remove:
            del self._cache[key]

    def set_theme(self, theme_name: str) -> None:
        """Activate ``theme_name`` and invalidate caches.

        Args:
            theme_name (str): Registered theme name.

        Returns:
            None
        """
        self._theme_manager.set_active_theme(theme_name)
        self._engine.set_theme(theme_name)
        self.invalidate_cache()

    def load_stylesheet(self, path: str) -> None:
        """Load an additional stylesheet from disk and invalidate caches.

        Args:
            path (str): Filesystem path to the stylesheet.

        Returns:
            None
        """
        self._engine.load_stylesheet(path)
        self.invalidate_cache()

    def load_stylesheet_text(self, name: str, text: str) -> None:
        """Load a stylesheet from raw text and invalidate caches.

        Args:
            name (str): Stylesheet identifier.
            text (str): Raw stylesheet content.

        Returns:
            None
        """

        self._engine.load_stylesheet_text(name, text)
        self.invalidate_cache()

    def clear_extra_stylesheets(self) -> None:
        """Remove all non-default stylesheets and invalidate caches."""

        self._engine.clear_extra_stylesheets()
        self.invalidate_cache()

    def resolve_styles_parallel(self, contexts: Sequence[StylingContext]) -> list[ResolvedStyle]:
        """Resolve styles for ``contexts`` using sequential fallback.

        Args:
            contexts (Sequence[StylingContext]): Styling contexts to resolve.

        Returns:
            list[ResolvedStyle]: Resolved styles in input order.
        """

        return [self.resolve_style(context) for context in contexts]

    def get_style_stats(self) -> dict[str, int]:
        """Return statistics about the styling subsystem cache.

        Returns:
            dict[str, int]: Statistics including cache size, theme version, and resolution count.
        """

        return {
            "cache_size": len(self._cache),
            "total_resolutions": self._resolution_counter.get(),
            "theme_version": self._theme_manager.version,
            "style_version": self._engine.theme_version,
        }

    def get_engine(self) -> StyleEngine:
        """Return the underlying style engine instance.

        Returns:
            StyleEngine: Managed style engine.
        """

        return self._engine

    def get_resolved_color(self, style: ResolvedStyle, property_name: str) -> ColorBlend | ColorSpec | None:
        """Extract a color value from a resolved style for GUI rendering.

        Args:
            style (ResolvedStyle): The resolved style to extract from.
            property_name (str): The color property name (e.g., 'color', 'background', 'border_color').

        Returns:
            str | None: Color specification or None if not set.
        """

        if property_name == "background_color":
            return style.background
        elif property_name == "border_color":
            return style.border_color
        elif property_name == "outline_color":
            return style.outline
        elif property_name == "text_decoration_color":
            return style.text_decoration_color
        else:
            # For generic color properties, try direct attribute access
            return getattr(style, property_name, None)

    def get_resolved_border(self, style: ResolvedStyle) -> tuple[float, str | None, str | None] | None:
        """Extract border information from a resolved style for GUI rendering.

        Args:
            style (ResolvedStyle): The resolved style to extract from.

        Returns:
            tuple[float, str, str | None] | None: (width, style, color) or None if no border.
        """

        if style.border is None:
            return None
        return (style.border.width, style.border.style, style.border.color)

    def get_resolved_font(self, style: ResolvedStyle) -> dict[str, str | int | None]:
        """Extract font information from a resolved style for GUI rendering.

        Args:
            style (ResolvedStyle): The resolved style to extract from.

        Returns:
            dict[str, str | int | None]: Font properties including family, size, and weight.
        """

        font_family: str | None = None
        font_weight = style.weight
        font_size: int | None = self._length_to_px(style.font_size)

        if style.font:
            fonts = self._get_font_registry()
            profile = fonts.get(style.font)
            if profile:
                font_family = profile.family or style.font
                if profile.weight is not None and font_weight is None:
                    font_weight = profile.weight
                if profile.size is not None and font_size is None:
                    font_size = int(profile.size)
            elif font_family is None:
                font_family = style.font

        return {
            "font_family": font_family,
            "font_size": font_size,
            "font_weight": font_weight,
        }

    def get_resolved_dimensions(self, style: ResolvedStyle) -> dict[str, float | None]:
        """Extract dimension information from a resolved style for GUI rendering.

        Args:
            style (ResolvedStyle): The resolved style to extract from.

        Returns:
            dict[str, float | None]: Dimension properties including width, height, etc.
        """

        return {
            "width": style.width.value if style.width else None,
            "height": style.height.value if style.height else None,
            "min_width": style.min_width.value if style.min_width else None,
            "min_height": style.min_height.value if style.min_height else None,
            "max_width": style.max_width.value if style.max_width else None,
            "max_height": style.max_height.value if style.max_height else None,
        }

    def get_resolved_spacing(self, style: ResolvedStyle) -> dict[str, tuple[float, ...] | None]:
        """Extract spacing information from a resolved style for GUI rendering.

        Args:
            style (ResolvedStyle): The resolved style to extract from.

        Returns:
            dict[str, tuple[float, ...] | None]: Spacing properties including padding, margin, etc.
        """

        def insets_to_tuple(insets: Insets | None) -> tuple[float, float, float, float] | None:
            if insets is None:
                return None
            return (insets.top.value, insets.right.value, insets.bottom.value, insets.left.value)

        return {
            "padding": insets_to_tuple(style.padding),
            "margin": insets_to_tuple(style.margin),
            "border_radius": insets_to_tuple(style.border_radius),
        }

    def _get_font_registry(self) -> dict[str, FontDef]:
        """Return a cached font registry synchronized with the style engine."""
        with self._font_registry_lock:
            version = self._engine.theme_version
            if version != self._font_registry_version:
                self._font_registry = self._engine.get_registered_fonts()
                self._font_registry_version = version
        return self._font_registry

    @staticmethod
    def _length_to_px(length: Length | None) -> int | None:
        """Convert a Length to pixels when possible."""
        if length is None:
            return None
        if length.unit == "px":
            return int(length.value)
        return None


_subsystem: StylingRuntime | None = None
_subsystem_lock = threading.RLock()


def get_styling_runtime() -> StylingRuntime:
    """Return the process-wide :class:`StylingRuntime`.

    Returns:
        StylingRuntime: Shared runtime instance.
    """
    global _subsystem
    if _subsystem is None:
        with _subsystem_lock:
            if _subsystem is None:
                _subsystem = StylingRuntime()
    return _subsystem


def resolve_component_style(
    component_name: str,
    *,
    state: Mapping[str, bool] | None = None,
    theme_overrides: Mapping[str, str] | None = None,
    caps: Any | None = None,
) -> ResolvedStyle:
    """Resolve a component style using the global subsystem.

    Args:
        component_name (str): Component identifier.
        state (Mapping[str, bool] | None): Optional state flags.
        theme_overrides (Mapping[str, str] | None): Theme overrides applied during resolution.
        caps (Any | None): Optional capability descriptor.

    Returns:
        ResolvedStyle: Resolved style instance.
    """
    from ornata.api.exports.definitions import StylingContext

    subsystem = get_styling_runtime()
    context = StylingContext(component_name, state, theme_overrides, caps)
    return subsystem.resolve_style(context)


def _caps_signature(caps: Any) -> int:
    depth = _safe_call(caps, "color_depth")
    dpi = _safe_call(caps, "dpi")
    metrics = _safe_call(caps, "cell_metrics")
    return hash((depth, dpi, metrics))


def _safe_call(obj: Any, attribute: str) -> str:
    if obj is None:
        return "?"
    try:
        candidate: Any = getattr(obj, attribute)
    except AttributeError:
        return "?"
    try:
        return repr(candidate()) if callable(candidate) else repr(candidate)
    except Exception:
        return "?"


def resolve_backend_component_style(
    component_name: str,
    *,
    state: Mapping[str, bool] | None = None,
    theme_overrides: Mapping[str, str] | None = None,
    caps: Any | None = None,
    backend: BackendTarget = BackendTarget.GUI,
) -> BackendStylePayload:
    """Resolve a component style for a specific backend using the global subsystem.

    Args:
        component_name (str): Component identifier.
        state (Mapping[str, bool] | None): Optional state flags.
        theme_overrides (Mapping[str, str] | None): Theme overrides applied during resolution.
        caps (Any | None): Optional capability descriptor.
        backend (BackendTarget): Target backend (default: GUI).

    Returns:
        BackendStylePayload: Backend-conditioned styling bundle.
    """
    from ornata.api.exports.definitions import StylingContext

    subsystem = get_styling_runtime()
    context = StylingContext(
        component_name=component_name,
        state=state,
        theme_overrides=theme_overrides,
        caps=caps,
        backend=backend,
    )
    return subsystem.resolve_backend_style(context)


__all__ = [
    "StylingRuntime",
    "resolve_component_style",
    "resolve_backend_component_style",
    "get_styling_runtime",
]
