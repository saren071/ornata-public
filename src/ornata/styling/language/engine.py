"""Runtime style engine for the Ornata Styling subsystem."""

from __future__ import annotations

import threading
from dataclasses import fields
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import STYLING_CACHE_LIMIT
from ornata.api.exports.utils import ThreadSafeLRUCache, get_logger

if TYPE_CHECKING:
    from collections.abc import Mapping

    from ornata.api.exports.definitions import CacheKey, FontDef, ResolvedStyle, Stylesheet


class StyleEngine:
    """Parse, cache, and resolve Ornata Style (OSTS) stylesheets."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._cache: ThreadSafeLRUCache[CacheKey, ResolvedStyle] = ThreadSafeLRUCache(max_size=STYLING_CACHE_LIMIT)
        self._sheets: list[Stylesheet] = []
        self._default_sheet: Stylesheet | None = None
        self._use_default = True
        self._version = 0
        self._logger = get_logger(__name__)
        # Incremental resolution cache for repeated component types
        self._component_cache: dict[str, ResolvedStyle] = {}
        self._load_default_stylesheet()

    @property
    def theme_version(self) -> int:
        return self._version

    def load_stylesheet(self, path: str | Path) -> None:
        """Load and parse a OSTS stylesheet from disk."""
        path_obj = Path(path)
        text = path_obj.read_text(encoding="utf-8")
        self.load_stylesheet_text(path_obj.name, text)

    def load_stylesheet_text(self, name: str, text: str) -> None:
        """Load a stylesheet from raw OSTS source."""
        from ornata.styling.language import diag
        from ornata.styling.language.grammar import parse_stylesheet
        self._logger.debug(f"Parsing stylesheet '{name}' ({len(text)} chars)")
        diag.clear()
        sheet = parse_stylesheet(name, text)
        warnings = diag.last_warnings()
        for message in warnings:
            self._logger.warning(f"{name}: {message}")

        with self._lock:
            self._sheets.append(sheet)
            self._use_default = False
            self._version += 1
            self._invalidate_cache_unlocked()
            self._logger.debug(
                "Registered stylesheet '%s' (total sheets: %d, version: %d)",
                name,
                len(self._sheets),
                self._version,
            )

    def clear_styles(self) -> None:
        """Remove all user-provided stylesheets and revert to defaults."""
        with self._lock:
            self._logger.debug("Clearing user stylesheets and resetting cache")
            self._sheets.clear()
            self._use_default = True
            self._version += 1
            self._invalidate_cache_unlocked()

    def resolve(self, *, node: Any, state: Mapping[str, bool], caps: Any, overrides: Mapping[str, str] | None = None) -> ResolvedStyle:
        """Resolve the merged style for a component node."""
        from ornata.api.exports.definitions import ResolvedStyle
        component = _extract_component_name(node)
        if not component:
            self._logger.warning("Unable to resolve style for node without component name: %r", node)
            return ResolvedStyle()

        active_states = frozenset(key for key, value in state.items() if value)
        caps_signature = _caps_signature(caps)

        with self._lock:
            from ornata.api.exports.definitions import CacheKey
            key = CacheKey(
                component=component,
                states=active_states,
                overrides=tuple(),
                style_version=self._version,
                theme_version=self._version,
                caps_signature=caps_signature,
            )
            cached: Any = self._cache.get(key)  # Any justified for dynamic cache data
            if cached is not None:
                self._logger.debug("Style cache hit for %s (states=%s)", component, sorted(active_states))
                return cached

            # Check incremental cache for base component style (no states)
            base_component = self._component_cache.get(component)
            if base_component is not None and not active_states:
                self._logger.debug("Incremental cache hit for %s", component)
                with self._lock:
                    self._cache[key] = base_component
                return base_component

            default_sheet = self._default_sheet if self._use_default else None
            sheets_snapshot = list(self._sheets)
            version = self._version

        self._logger.debug(
            "Resolving style for %s (states=%s, sheets=%d, version=%d)",
            component,
            sorted(active_states),
            len(sheets_snapshot) + (1 if default_sheet else 0),
            version,
        )

        resolved = self._resolve_from_sheets(
            component=component,
            active_states=active_states,
            default_sheet=default_sheet,
            sheets=sheets_snapshot,
            caps=caps,
        )

        self._cache[key] = resolved
        # Cache base component style for incremental resolution
        if not active_states:
            self._component_cache[component] = resolved
        return resolved

    def get_registered_fonts(self) -> dict[str, FontDef]:
        """Return a merged mapping of all registered fonts across active stylesheets.

        Returns:
            dict[str, FontDef]: Mapping of font token -> font definition.
        """
        with self._lock:
            fonts: dict[str, FontDef] = {}
            if self._default_sheet is not None:
                fonts.update(self._default_sheet.fonts)
            for sheet in self._sheets:
                fonts.update(sheet.fonts)
            return dict(fonts)

    def _resolve_from_sheets(
        self,
        *,
        component: str,
        active_states: frozenset[str],
        default_sheet: Stylesheet | None,
        sheets: list[Stylesheet],
        caps: Any,
    ) -> ResolvedStyle:
        from ornata.api.exports.definitions import ResolvedStyle
        resolved = ResolvedStyle()
        inherited_custom_props: dict[str, str] = {}
        accumulated_keyframes: dict[str, Any] = {}

        active_sheets: list[Stylesheet] = []
        if default_sheet is not None:
            active_sheets.append(default_sheet)
        active_sheets.extend(sheets)

        for sheet in active_sheets:
            # build plain color map (token name -> hex/string)
            colors_map = {name: tok.value for name, tok in sheet.colors.items()}
            fonts_map = sheet.fonts  # FontDef instances are fine as-is
            from ornata.styling.language.cascade import resolve_stylesheet

            partial = resolve_stylesheet(
                sheet=sheet,
                component=component,
                states=active_states,
                colors=colors_map,
                fonts=fonts_map,
            )
            if partial.custom_properties:
                inherited_custom_props.update(partial.custom_properties)
            if partial.keyframes:
                accumulated_keyframes.update(partial.keyframes)
            resolved = _merge_styles(resolved, partial)

        return resolved

    def _load_default_stylesheet(self) -> None:
        assets_dir = Path(__file__).resolve().parent.parent / "theming" / "assets"
        default_path = assets_dir / "defaults.osts"
        fallback_path = assets_dir / "default.osts"

        try:
            path = default_path if default_path.exists() else fallback_path
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            self._logger.error("Default theme file is missing (looked for %s)", default_path)
            return

        self._logger.debug("Loading built-in theme from %s", path.name)
        from ornata.styling.language import diag
        from ornata.styling.language.grammar import parse_stylesheet
        diag.clear()
        sheet = parse_stylesheet(path.name, text)
        warnings = diag.last_warnings()
        for message in warnings:
            self._logger.warning(f"{path.name}: {message}")

        with self._lock:
            self._default_sheet = sheet
            self._use_default = True
            self._version += 1
            self._invalidate_cache_unlocked()

    def _invalidate_cache_unlocked(self) -> None:
        self._cache.clear()
        self._component_cache.clear()

    # ADD no-op compatibility methods used by the public facade
    def set_theme(self, theme_name: str) -> None:
        # No themed bundles yet; bump version so caches invalidate consistently
        with self._lock:
            self._version += 1
            self._invalidate_cache_unlocked()

    def clear_extra_stylesheets(self) -> None:
        # Alias to existing clear that re-enables default sheet
        self.clear_styles()


def _merge_styles(base: ResolvedStyle, update: ResolvedStyle) -> ResolvedStyle:
    from ornata.api.exports.definitions import ResolvedStyle
    values: dict[str, Any] = {}
    for field in fields(ResolvedStyle):
        new_value: Any = getattr(update, field.name)
        if new_value is not None:
            values[field.name] = new_value
        else:
            values[field.name] = getattr(base, field.name)
    return ResolvedStyle(**values)


def _caps_signature(caps: Any) -> int:
    depth: Any = _safe_call(caps, "color_depth")
    dpi: Any = _safe_call(caps, "dpi")
    metrics: Any = _safe_call(caps, "cell_metrics")
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


def _extract_component_name(node: Any) -> str | None:
    if isinstance(node, dict):
        component: Any = node.get("component_name")
        if isinstance(component, str) and component:
            return component
    component = getattr(node, "component_name", None)
    if isinstance(component, str) and component:
        return component
    cls: Any = getattr(node, "__class__", None)
    name: Any = getattr(cls, "__name__", None)
    return name if isinstance(name, str) else None


__all__ = ["StyleEngine"]
