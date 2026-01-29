"""High level colour resolution services used by the Styling runtime."""

from __future__ import annotations

import re
from collections import OrderedDict
from threading import RLock
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.definitions.dataclasses.styling import HSLA, RGBA, ColorBlend, ColorFunction

_T = TypeVar("_T")


class BoundedCache[T]:
    """Thread-safe bounded cache with simple eviction."""

    def __init__(self, limit: int) -> None:
        self._limit = max(1, limit)
        self._data: OrderedDict[str, Any] = OrderedDict()
        self._lock = RLock()

    def get(self, key: str) -> Any | None:
        """Return the cached value for ``key`` when available."""

        with self._lock:
            value = self._data.get(key)
            if value is not None:
                self._data.move_to_end(key)
            return value

    def put(self, key: str, value: Any) -> None:
        """Store ``value`` under ``key`` evicting the oldest entry when needed."""

        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
                self._data[key] = value
                return
            if len(self._data) >= self._limit:
                self._data.popitem(last=False)
            self._data[key] = value

    def clear(self) -> None:
        """Remove all cached entries."""

        with self._lock:
            self._data.clear()


class ColorResolver:
    """Resolve colour specifications into ANSI codes and RGB tuples."""

    def __init__(
        self,
        *,
        theme_lookup: Callable[[str], str | None] | None = None,
        theme_version_provider: Callable[[], int] | None = None,
    ) -> None:
        """Create a resolver bound to the active theming system.

        Args:
            theme_lookup (Callable[[str], str | None] | None): Resolve theme tokens to colour specs.
            theme_version_provider (Callable[[], int] | None): Provide the current theme version.
        """
        from ornata.definitions.constants import ANSI_CACHE_LIMIT, BACKGROUND_CACHE_LIMIT, GRADIENT_CACHE_LIMIT, RGB_CACHE_LIMIT

        self._theme_lookup: Callable[[str], str | None] = theme_lookup or (lambda token: None)
        self._version_provider = theme_version_provider or None
        self._last_version = -1

        self._ansi_cache: BoundedCache[str] = BoundedCache(ANSI_CACHE_LIMIT)
        self._background_cache: BoundedCache[str] = BoundedCache(BACKGROUND_CACHE_LIMIT)
        self._rgb_cache: BoundedCache[tuple[int, int, int]] = BoundedCache(RGB_CACHE_LIMIT)
        self._gradient_cache: BoundedCache[str] = BoundedCache(GRADIENT_CACHE_LIMIT)

    def resolve_ansi(self, spec: str | RGBA | HSLA | ColorFunction | ColorBlend | None) -> str:
        """Resolve ``spec`` to a foreground ANSI sequence."""
        from ornata.definitions.dataclasses.styling import HSLA, RGBA, ColorBlend, ColorFunction
        from ornata.styling.colorkit.ansi import AnsiConverter
        from ornata.styling.colorkit.spaces import ColorSpaces

        self._ensure_theme_cache_current()
        if spec is None:
            return ""

        if isinstance(spec, RGBA):
            rgb = (spec.r, spec.g, spec.b)
            return AnsiConverter.rgb_to_ansi(rgb)

        if isinstance(spec, HSLA):
            rgb = ColorSpaces.hsl_to_rgb((spec.h, spec.s, spec.lightness))
            return AnsiConverter.rgb_to_ansi(rgb)

        if isinstance(spec, ColorFunction):
            return self._resolve_function(spec)

        if isinstance(spec, ColorBlend):
            rgb = self.resolve_rgb(spec.color_a)
            return AnsiConverter.rgb_to_ansi(rgb) if rgb else ""

        key = self._normalize_spec(spec)
        cached = self._ansi_cache.get(key)
        if cached is not None:
            return cached

        resolved = self._resolve_string_spec(key)
        self._ansi_cache.put(key, resolved)
        return resolved

    def resolve_background(self, spec: str | None) -> str:
        """Resolve ``spec`` to a background ANSI sequence."""

        self._ensure_theme_cache_current()
        if spec is None:
            return ""

        key = f"bg::{self._normalize_spec(spec)}"
        cached = self._background_cache.get(key)
        if cached is not None:
            return cached

        resolved = self._resolve_background_string(spec)
        self._background_cache.put(key, resolved)
        return resolved

    def resolve_rgb(self, spec: str | RGBA | HSLA | ColorFunction | ColorBlend | None) -> tuple[int, int, int] | None:
        """Resolve ``spec`` to an RGB tuple."""
        from ornata.definitions.dataclasses.styling import HSLA, RGBA, ColorBlend, ColorFunction
        from ornata.styling.colorkit.spaces import ColorSpaces

        self._ensure_theme_cache_current()
        if spec is None:
            return None

        if isinstance(spec, RGBA):
            return (spec.r, spec.g, spec.b)

        if isinstance(spec, HSLA):
            return ColorSpaces.hsl_to_rgb((spec.h, spec.s, spec.lightness))

        if isinstance(spec, ColorFunction):
            return None

        if isinstance(spec, ColorBlend):
            return self.resolve_rgb(spec.color_a)

        key = self._normalize_spec(spec)
        cached = self._rgb_cache.get(key)
        if cached is not None:
            return cached

        resolved = self._resolve_rgb_from_string(key)
        if resolved is not None:
            self._rgb_cache.put(key, resolved)
        return resolved

    def gradient(self, text: str, start_color: tuple[int, int, int], end_color: tuple[int, int, int]) -> str:
        """Return ``text`` decorated with a linear gradient."""
        from ornata.styling.colorkit.gradients import GradientRenderer
        from ornata.styling.colorkit.palette import PaletteLibrary

        cache_key = f"{start_color}-{end_color}-{text}"
        cached = self._gradient_cache.get(cache_key)
        if cached is not None:
            return cached

        rendered = GradientRenderer.render_gradient(text, start_color, end_color)
        hidden = f"\033[8m{text}\033[0m"
        output = f"{rendered}{hidden}{PaletteLibrary.get_effect('reset')}"
        self._gradient_cache.put(cache_key, output)
        return output

    def invalidate(self) -> None:
        """Clear cached data (typically triggered on theme change)."""

        self._ansi_cache.clear()
        self._background_cache.clear()
        self._rgb_cache.clear()
        self._gradient_cache.clear()

    def _resolve_string_spec(self, spec: str) -> str:
        """Resolve bare string specifications with fast-path dispatch."""
        from ornata.definitions.constants import EFFECTS, NAMED_COLORS
        from ornata.styling.colorkit.ansi import AnsiConverter
        from ornata.styling.colorkit.palette import PaletteLibrary
        if not spec:
            return ""

        # var(...) and $token first
        if spec.startswith("var(") and spec.endswith(")"):
            token = spec[4:-1].strip()
            resolved = self._theme_lookup(token)
            return self.resolve_ansi(resolved) if resolved else ""
        if spec.startswith("$"):
            resolved = self._theme_lookup(spec[1:])
            return self.resolve_ansi(resolved) if resolved else ""

        # Named shortcuts
        if spec in NAMED_COLORS:
            return PaletteLibrary.get_named_color(spec)
        if spec in EFFECTS:
            return PaletteLibrary.get_effect(spec)

        # Ultra-cheap first-character routing to avoid regex cascade
        c0 = spec[0]
        if c0 == "#":
            return AnsiConverter.hex_to_ansi(spec)
        if c0 == "r":
            # rgb(...) / rgba(...)
            if spec.startswith("rgb(") and spec.endswith(")"):
                return AnsiConverter.rgb_str_to_ansi(spec[4:-1])
            if spec.startswith("rgba(") and spec.endswith(")"):
                inner = spec[5:-1]
                rgb_part = ",".join(inner.split(",", 3)[:3])
                return AnsiConverter.rgb_str_to_ansi(rgb_part)
        if c0 == "h":
            # hsl(...) / hsla(...)
            if spec.startswith("hsl(") and spec.endswith(")"):
                rgb = self._hsl_string_to_rgb(spec)
                return AnsiConverter.rgb_to_ansi(rgb) if rgb else ""
            if spec.startswith("hsla(") and spec.endswith(")"):
                rgb = self._hsla_string_to_rgb(spec)
                return AnsiConverter.rgb_to_ansi(rgb) if rgb else ""
        if c0 == "a" and spec.startswith("ansi") and spec[4:].isdigit():
            idx = int(spec[4:])
            if 0 <= idx <= 15:
                base = 30 + (idx % 8) + (60 if idx >= 8 else 0)
                return f"\033[{base}m"

        # Comma form 'r,g,b'
        if "," in spec:
            return AnsiConverter.rgb_str_to_ansi(spec)

        # Theme fallback
        resolved = self._theme_lookup(spec)
        if resolved:
            return self.resolve_ansi(resolved)
        return ""

    def _resolve_background_string(self, spec: str) -> str:
        """Resolve background colour specifications with fast-paths."""
        from ornata.definitions.constants import BACKGROUND_COLORS
        from ornata.styling.colorkit.ansi import AnsiConverter
        s = self._normalize_spec(spec)

        # bg#... / bg:... / direct named backgrounds
        if s.startswith("bg#"):
            return AnsiConverter.hex_to_bg_ansi(s[2:])
        if s.startswith("bg:"):
            return AnsiConverter.rgb_str_to_bg_ansi(s[3:])
        if s in BACKGROUND_COLORS:
            return BACKGROUND_COLORS[s]

        # #rrggbb / r,g,b
        if s.startswith("#"):
            return AnsiConverter.hex_to_bg_ansi(s)
        if "," in s:
            return AnsiConverter.rgb_str_to_bg_ansi(s)

        # Theme & FG-to-BG transform fallback
        resolved = self._theme_lookup(s)
        if resolved:
            return self.resolve_background(resolved)

        fg = self.resolve_ansi(s)
        return fg.replace("[38;", "[48;") if "[38;" in fg else ""

    def _resolve_rgb_from_string(self, spec: str) -> tuple[int, int, int] | None:
        """Resolve RGB tuple from a string specification with minimal regex."""
        from ornata.definitions.constants import NAMED_COLORS, NAMED_HEX
        from ornata.styling.colorkit.ansi import AnsiConverter
        from ornata.styling.colorkit.palette import PaletteLibrary
        # named hex map
        if spec in NAMED_HEX:
            hex_value = PaletteLibrary.get_named_hex(spec)
            return AnsiConverter.hex_to_rgb(hex_value) if hex_value else None

        c0 = spec[0]
        if c0 == "#":
            return AnsiConverter.hex_to_rgb(spec)
        if "," in spec:
            return AnsiConverter.parse_rgb_string(spec)
        if c0 == "r":
            if spec.startswith("rgb(") and spec.endswith(")"):
                return AnsiConverter.parse_rgb_string(spec[4:-1])
            if spec.startswith("rgba(") and spec.endswith(")"):
                inner = spec[5:-1]
                return AnsiConverter.parse_rgb_string(",".join(inner.split(",", 3)[:3]))
        if c0 == "h":
            if spec.startswith("hsl(") and spec.endswith(")"):
                return self._hsl_string_to_rgb(spec)
            if spec.startswith("hsla(") and spec.endswith(")"):
                return self._hsla_string_to_rgb(spec)

        if spec in NAMED_COLORS:
            from ornata.definitions.constants import ANSI_4BIT_RGB
            # Best-effort 4-bit ANSI to approximate RGB
            ansi_code = PaletteLibrary.get_named_color(spec)
            m = re.search(r"\[(\d+)m", ansi_code)
            if m:
                rgb = ANSI_4BIT_RGB.get(m.group(1))
                if rgb:
                    return rgb

        resolved = self._theme_lookup(spec)
        if resolved:
            return self.resolve_rgb(resolved)
        return None

    def _hsl_string_to_rgb(self, spec: str) -> tuple[int, int, int] | None:
        """Convert an ``hsl()`` string to RGB."""
        from ornata.styling.colorkit.spaces import ColorSpaces

        inner = spec[4:-1]
        parts = [part.strip() for part in inner.split(",")]
        if len(parts) != 3:
            return None
        try:
            hue = float(parts[0])
            saturation = float(parts[1].rstrip("%")) / 100.0 if parts[1].endswith("%") else float(parts[1])
            lightness = float(parts[2].rstrip("%")) / 100.0 if parts[2].endswith("%") else float(parts[2])
        except ValueError:
            return None
        return ColorSpaces.hsl_to_rgb((hue, saturation, lightness))

    def _hsla_string_to_rgb(self, spec: str) -> tuple[int, int, int] | None:
        """Convert an ``hsla()`` string to RGB ignoring the alpha channel."""
        from ornata.styling.colorkit.spaces import ColorSpaces

        inner = spec[5:-1]
        parts = [part.strip() for part in inner.split(",")]
        if len(parts) < 3:
            return None
        try:
            hue = float(parts[0])
            saturation = float(parts[1].rstrip("%")) / 100.0 if parts[1].endswith("%") else float(parts[1])
            lightness = float(parts[2].rstrip("%")) / 100.0 if parts[2].endswith("%") else float(parts[2])
        except ValueError:
            return None
        return ColorSpaces.hsl_to_rgb((hue, saturation, lightness))

    def _resolve_function(self, function: ColorFunction) -> str:
        """Resolve functional colour constructs."""
        from ornata.styling.colorkit.ansi import AnsiConverter
        from ornata.styling.colorkit.spaces import ColorSpaces

        if function.name == "color-mix" and len(function.args) >= 2:
            anchor = self.resolve_rgb(function.args[0])
            blend = self.resolve_rgb(function.args[1])
            if anchor and blend:
                rgb = ColorSpaces.blend(anchor, blend, 0.5)
                return AnsiConverter.rgb_to_ansi(rgb)
        return ""

    def _normalize_spec(self, spec: str | Any) -> str:
        """Return a normalised string key for caching."""

        if isinstance(spec, str):
            return spec.strip().lower()
        return str(spec).strip().lower()

    def _ensure_theme_cache_current(self) -> None:
        """Invalidate caches when the theme version changes (fast local binding)."""
        provider = self._version_provider
        if provider is None:
            return
        current_version = provider()
        if current_version != self._last_version:
            self.invalidate()
            self._last_version = current_version


__all__ = ["ColorResolver", "BoundedCache"]
