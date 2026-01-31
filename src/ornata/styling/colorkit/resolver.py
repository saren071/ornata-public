"""High level colour resolution services used by the Styling runtime."""

from __future__ import annotations

from collections import OrderedDict
from threading import RLock
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.definitions.dataclasses.styling import (
        HSLA,
        RGBA,
        ColorBlend,
        ColorFunction,
        ColorLiteral,
    )

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

    def resolve_ansi(
        self,
        spec: str | RGBA | HSLA | ColorFunction | ColorBlend | ColorLiteral | None,
    ) -> str:
        """Resolve ``spec`` to a foreground ANSI sequence."""
        from ornata.definitions.dataclasses.styling import (
            HSLA,
            RGBA,
            ColorBlend,
            ColorFunction,
            ColorLiteral,
        )
        from ornata.styling.colorkit.ansi import AnsiConverter
        from ornata.styling.colorkit.spaces import ColorSpaces

        self._ensure_theme_cache_current()
        if spec is None:
            return ""

        if isinstance(spec, ColorLiteral):
            return self._color_literal_to_ansi(spec)

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

    def resolve_rgb(
        self,
        spec: str | RGBA | HSLA | ColorFunction | ColorBlend | ColorLiteral | None,
    ) -> tuple[int, int, int] | None:
        """Resolve ``spec`` to an RGB tuple."""
        from ornata.definitions.dataclasses.styling import (
            HSLA,
            RGBA,
            ColorBlend,
            ColorFunction,
            ColorLiteral,
        )
        from ornata.styling.colorkit.spaces import ColorSpaces

        self._ensure_theme_cache_current()
        if spec is None:
            return None

        if isinstance(spec, ColorLiteral):
            return spec.to_rgb()

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
        from ornata.definitions.constants import EFFECTS
        from ornata.styling.colorkit.ansi import AnsiConverter
        from ornata.styling.colorkit.named_colors import NAMED_COLORS
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
        spec_lower = spec.lower()
        if spec_lower in NAMED_COLORS:
            return AnsiConverter.hex_to_ansi(NAMED_COLORS[spec_lower])
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
        from ornata.styling.colorkit.ansi import AnsiConverter
        from ornata.styling.colorkit.named_colors import NAMED_COLORS
        # named color lookup
        spec_lower = spec.lower()
        if spec_lower in NAMED_COLORS:
            hex_value = NAMED_COLORS[spec_lower]
            return AnsiConverter.hex_to_rgb(hex_value)

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

        if spec_lower in NAMED_COLORS:
            # Resolve named color to RGB
            hex_value = NAMED_COLORS[spec_lower]
            return AnsiConverter.hex_to_rgb(hex_value)

        resolved = self._theme_lookup(spec)
        if resolved:
            return self.resolve_rgb(resolved)
        return None

    def _color_literal_to_ansi(self, literal: ColorLiteral) -> str:
        """Convert a ColorLiteral to an ANSI escape sequence.

        Args:
            literal: The color literal to convert.

        Returns:
            ANSI escape sequence string.
        """
        from ornata.styling.colorkit.ansi import AnsiConverter

        rgb = literal.to_rgb()
        if rgb:
            return AnsiConverter.rgb_to_ansi(rgb)
        return ""

    def to_cli(self, literal: ColorLiteral) -> str:
        """Convert a ColorLiteral to CLI/terminal ANSI format.

        Args:
            literal: The color literal to convert.

        Returns:
            ANSI escape sequence for terminal output.
        """
        return self._color_literal_to_ansi(literal)

    def to_gui(self, literal: ColorLiteral) -> str | tuple[int, int, int] | None:
        """Convert a ColorLiteral to GUI-ready format.

        For GUI backends, we preserve the original color data.
        Returns hex string or RGB tuple that GUI renderers can use directly.

        Args:
            literal: The color literal to convert.

        Returns:
            Hex string, RGB tuple, or None if conversion fails.
        """
        if literal.kind == "hex":
            return literal.value if isinstance(literal.value, str) else None
        return literal.to_rgb()

    def resolve_literal(self, spec: str, palette: dict[str, ColorLiteral] | None = None) -> ColorLiteral | None:
        """Resolve a color specification to a ColorLiteral.

        This method parses color strings (hex, rgb, named colors, refs)
        and returns a renderer-agnostic ColorLiteral.

        Args:
            spec: Color specification string (e.g., "#ff0000", "rgb(255,0,0)", "red", "var(primary)")
            palette: Optional palette dictionary for resolving refs.

        Returns:
            ColorLiteral or None if the spec cannot be resolved.
        """
        from ornata.definitions.dataclasses.styling import ColorLiteral
        from ornata.styling.colorkit.named_colors import NAMED_COLORS

        if not spec:
            return None

        spec = spec.strip()

        # Handle var(...) references
        if spec.startswith("var(") and spec.endswith(")"):
            token = spec[4:-1].strip()
            if palette and token in palette:
                return palette[token]
            theme_resolved = self._theme_lookup(token)
            if theme_resolved:
                return self.resolve_literal(theme_resolved, palette)
            return None

        # Handle $token references
        if spec.startswith("$"):
            token = spec[1:]
            if palette and token in palette:
                return palette[token]
            theme_resolved = self._theme_lookup(token)
            if theme_resolved:
                return self.resolve_literal(theme_resolved, palette)
            return None

        # Hex colors
        if spec.startswith("#"):
            return ColorLiteral(kind="hex", value=spec)

        # rgb(...) and rgba(...)
        if spec.startswith("rgb(") and spec.endswith(")"):
            rgb_tuple = self._parse_rgb_tuple(spec[4:-1])
            if rgb_tuple:
                return ColorLiteral(kind="rgb", value=rgb_tuple)
        if spec.startswith("rgba(") and spec.endswith(")"):
            rgba_tuple = self._parse_rgba_tuple(spec[5:-1])
            if rgba_tuple:
                return ColorLiteral(kind="rgba", value=rgba_tuple)

        # hsl(...) and hsla(...)
        if spec.startswith("hsl(") and spec.endswith(")"):
            hsl_tuple = self._parse_hsl_tuple(spec[4:-1])
            if hsl_tuple:
                return ColorLiteral(kind="hsl", value=hsl_tuple)
        if spec.startswith("hsla(") and spec.endswith(")"):
            hsla_tuple = self._parse_hsla_tuple(spec[5:-1])
            if hsla_tuple:
                return ColorLiteral(kind="hsla", value=hsla_tuple)

        # Named colors from CSS palette
        spec_lower = spec.lower()
        if spec_lower in NAMED_COLORS:
            return ColorLiteral(kind="named", value=NAMED_COLORS[spec_lower])

        # Palette lookup
        if palette and spec_lower in palette:
            return palette[spec_lower]

        # Theme lookup
        theme_resolved = self._theme_lookup(spec)
        if theme_resolved:
            return self.resolve_literal(theme_resolved, palette)

        return None

    def _parse_rgb_tuple(self, inner: str) -> tuple[int, int, int] | None:
        """Parse RGB values from inside rgb() parentheses."""
        parts = [p.strip() for p in inner.split(",")]
        if len(parts) != 3:
            return None
        try:
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            return None

    def _parse_rgba_tuple(self, inner: str) -> tuple[int, int, int, float] | None:
        """Parse RGBA values from inside rgba() parentheses."""
        parts = [p.strip() for p in inner.split(",")]
        if len(parts) != 4:
            return None
        try:
            return (int(parts[0]), int(parts[1]), int(parts[2]), float(parts[3]))
        except ValueError:
            return None

    def _parse_hsl_tuple(self, inner: str) -> tuple[float, float, float] | None:
        """Parse HSL values from inside hsl() parentheses."""
        parts = [p.strip() for p in inner.split(",")]
        if len(parts) != 3:
            return None
        try:
            h = float(parts[0])
            s = float(parts[1].rstrip("%")) / 100.0 if parts[1].endswith("%") else float(parts[1])
            lightness_val = float(parts[2].rstrip("%")) / 100.0 if parts[2].endswith("%") else float(parts[2])
            return (h, s, lightness_val)
        except ValueError:
            return None

    def _parse_hsla_tuple(self, inner: str) -> tuple[float, float, float, float] | None:
        """Parse HSLA values from inside hsla() parentheses."""
        parts = [p.strip() for p in inner.split(",")]
        if len(parts) != 4:
            return None
        try:
            h = float(parts[0])
            s = float(parts[1].rstrip("%")) / 100.0 if parts[1].endswith("%") else float(parts[1])
            lightness_val = float(parts[2].rstrip("%")) / 100.0 if parts[2].endswith("%") else float(parts[2])
            a = float(parts[3])
            return (h, s, lightness_val, a)
        except ValueError:
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
        rgb = ColorSpaces.hsl_to_rgb((hue, saturation, lightness))
        if rgb:
            return (int(rgb[0]), int(rgb[1]), int(rgb[2]))
        return None

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
        rgb = ColorSpaces.hsl_to_rgb((hue, saturation, lightness))
        if rgb:
            return (int(rgb[0]), int(rgb[1]), int(rgb[2]))
        return None

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
