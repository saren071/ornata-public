"""Theme management for the Ornata styling system."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from ornata.api.exports.definitions import Theme

logger = get_logger(__name__)

class ThemeManager:
    """Load, register, and resolve OSTS themes.

    The ThemeManager handles the complete lifecycle of themes in Ornata's styling system:

    1. **Theme Discovery**: Automatically discovers and loads built-in themes from the assets directory
    2. **Theme Registration**: Allows dynamic registration of themes from files, strings, or objects
    3. **Theme Resolution**: Resolves color tokens through a fallback hierarchy:
       - Active theme palette
       - Defaults theme palette
       - Named hex colors (e.g., "red" -> "#ef4444")
       - Named ANSI colors (e.g., "red" -> "\\033[91m")
    4. **Cache Invalidation**: Provides thread-safe cache invalidation when themes change
    5. **Theme Extension**: Supports creating derived themes with palette overrides

    Theme files use the .osts format with @colors and @fonts sections, followed by component style rules.
    """

    def __init__(self, theme_dir: Path | str | None = None) -> None:
        """Create a theme manager instance.

        Args:
            theme_dir (Path | str | None): Directory containing built-in themes.

        Returns:
            None
        """

        self._lock = threading.RLock()
        self._themes: dict[str, Theme] = {}
        self._active_theme: str | None = None
        self._version = 0
        self._theme_dir = Path(theme_dir) if theme_dir else Path(__file__).resolve().parent / "assets"
        self._cache_invalidators: list[Callable[[], None]] = []
        self._load_builtin_themes()

    @property
    def version(self) -> int:
        """Return the current theme version.

        Returns:
            int: Incremented whenever theme data changes.
        """

        with self._lock:
            return self._version

    def register_theme(self, theme: Theme, *, activate: bool = False) -> None:
        """Register ``theme`` and optionally activate it.

        Args:
            theme (Theme): Theme definition to register.
            activate (bool): Whether the theme should become active.

        Returns:
            None
        """

        with self._lock:
            self._themes[theme.name] = theme
            if activate or self._active_theme is None:
                self._active_theme = theme.name
                self.invalidate_caches()
            self._increment_version("registered theme %s", theme.name)

    def load_theme_file(self, path: Path | str, *, activate: bool = False) -> Theme:
        """Load a theme from the filesystem.

        Args:
            path (Path | str): Path to the ``.osts`` file.
            activate (bool): Whether to activate the loaded theme.

        Returns:
            Theme: Parsed theme instance.
        """

        theme_path = Path(path)
        content = theme_path.read_text(encoding="utf-8")
        theme = self._parse_theme(theme_path.stem, content)
        self.register_theme(theme, activate=activate)
        return theme

    def load_theme_text(self, name: str, content: str, *, activate: bool = False) -> Theme:
        """Load a theme from raw ``.osts`` text.

        Args:
            name (str): Theme identifier.
            content (str): Raw OSTS theme content.
            activate (bool): Whether to activate the loaded theme.

        Returns:
            Theme: Parsed theme instance.
        """

        theme = self._parse_theme(name, content)
        self.register_theme(theme, activate=activate)
        return theme

    def load_theme(self, name: str) -> Theme:
        """Load or activate a built-in theme by name.

        Args:
            name (str): Theme identifier to load.

        Returns:
            Theme: Loaded or activated theme instance.

        Raises:
            ValueError: When ``name`` is empty.
            FileNotFoundError: When the requested theme cannot be found.
        """

        normalized = name.strip()
        if not normalized:
            raise ValueError("Theme name must not be empty")

        with self._lock:
            target = normalized.lower()
            for registered_name, theme in self._themes.items():
                if registered_name.lower() == target:
                    self.set_active_theme(registered_name)
                    return theme

        path = self._find_theme_path(normalized)
        if path is None:
            raise FileNotFoundError(f"Theme '{name}' not found in {self._theme_dir}")

        return self.load_theme_file(path, activate=True)

    def set_active_theme(self, name: str) -> None:
        """Activate the theme named ``name``.

        Args:
            name (str): Registered theme name.

        Raises:
            ValueError: When the requested theme is not registered.

        Returns:
            None
        """

        with self._lock:
            if name not in self._themes:
                raise ValueError(f"Theme '{name}' is not registered")
            self._active_theme = name
            self.invalidate_caches()
            self._increment_version("activated theme %s", name)

    def get_active_theme(self) -> Theme | None:
        """Return the active theme instance.

        Returns:
            Theme | None: Active theme or ``None`` when unset.
        """

        with self._lock:
            if self._active_theme is None:
                return None
            return self._themes.get(self._active_theme)

    def list_themes(self) -> list[str]:
        """Return the names of all registered themes.

        Returns:
            list[str]: Sorted list of theme names.
        """

        with self._lock:
            return sorted(self._themes)

    def register_cache_invalidator(self, invalidator: Callable[[], None]) -> None:
        """Register a callback to invalidate caches when themes change.

        Args:
            invalidator (Callable[[], None]): Function to call when theme version changes.

        Returns:
            None
        """

        with self._lock:
            self._cache_invalidators.append(invalidator)

    def invalidate_caches(self) -> None:
        """Invalidate all registered caches.

        Returns:
            None
        """

        with self._lock:
            for invalidator in self._cache_invalidators:
                try:
                    invalidator()
                except Exception as exc:
                    logger.warning("Cache invalidator failed: %s", exc)

    def resolve_token(self, token: str) -> str | None:
        """Resolve a theme token to a colour specification.

        This method implements a hierarchical fallback system for color resolution:

        1. **Active Theme**: Check the currently active theme's palette
        2. **Defaults Theme**: Fall back to the built-in defaults theme
        3. **Named Hex Colors**: Use predefined hex values for common color names
        4. **Named ANSI Colors**: Fall back to ANSI escape sequences for terminal output

        Args:
            token (str): Token without ``$`` prefix (e.g., "primary", "red").

        Returns:
            str | None: Colour specification when available, None if token cannot be resolved.
        """
        from ornata.styling.colorkit.palette import PaletteLibrary

        normalized = token.strip().lower()
        with self._lock:
            candidates: list[Mapping[str, str]] = []
            active_theme = self.get_active_theme()
            if active_theme:
                candidates.append(active_theme.palette)
            defaults_theme = self._themes.get("defaults")
            if defaults_theme:
                candidates.append(defaults_theme.palette)

        for palette in candidates:
            if normalized in palette:
                return palette[normalized]

        named = PaletteLibrary.get_named_hex(normalized)
        if named:
            return named
        ansi_named = PaletteLibrary.get_named_color(normalized)
        return ansi_named or None

    def extend_theme(self, base_theme: str, overrides: Mapping[str, str], *, name: str | None = None) -> Theme:
        """Create a new theme based on ``base_theme`` with ``overrides`` applied.

        Args:
            base_theme (str): Existing theme name.
            overrides (Mapping[str, str]): Palette overrides.
            name (str | None): Optional new theme name.

        Returns:
            Theme: Newly registered theme instance.
        """
        from ornata.api.exports.definitions import Theme

        with self._lock:
            base = self._themes.get(base_theme)
            if base is None:
                raise ValueError(f"Theme '{base_theme}' is not registered")
            palette = dict(base.palette)
            for key, value in overrides.items():
                palette[key.lower()] = value
            extended_name = name or f"{base_theme}_override"
            theme = Theme(name=extended_name, palette=palette)
            self._themes[extended_name] = theme
            self.invalidate_caches()
            self._increment_version("extended theme %s -> %s", base_theme, extended_name)
            return theme

    def palette_for(self, name: str) -> Mapping[str, str] | None:
        """Return the palette for the given theme name.

        Args:
            name (str): Registered theme name.

        Returns:
            Mapping[str, str] | None: Palette mapping or ``None`` when missing.
        """

        with self._lock:
            theme = self._themes.get(name)
            return theme.palette if theme else None

    def _load_builtin_themes(self) -> None:
        """Discover built-in themes from the assets directory.

        Returns:
            None
        """

        if not self._theme_dir.exists():
            logger.warning("Theme asset directory %s does not exist", self._theme_dir)
            return

        for path in sorted(self._theme_dir.glob("*.osts")):
            try:
                self.load_theme_file(path, activate=False)
            except Exception as exc:
                logger.warning("Failed to load theme %s: %s", path.name, exc)

        if self._themes and self._active_theme is None:
            self._active_theme = next(iter(self._themes))

    def _find_theme_path(self, normalized: str) -> Path | None:
        """Return a theme asset path for ``normalized`` when available.

        Args:
            normalized (str): Case-insensitive theme identifier.

        Returns:
            Path | None: Theme file path when found, otherwise ``None``.
        """

        lower_name = normalized.lower()
        candidate = self._theme_dir / f"{normalized}.osts"
        if candidate.exists():
            return candidate
        for theme_path in self._theme_dir.glob("*.osts"):
            if theme_path.stem.lower() == lower_name:
                return theme_path
        return None

    def _parse_theme(self, name: str, content: str) -> Theme:
        """Parse raw OSTS theme content into a :class:`Theme`.

        Args:
            name (str): Theme name.
            content (str): Raw OSTS content.

        Returns:
            Theme: Parsed theme instance.
        """
        from ornata.api.exports.definitions import Theme

        palette: dict[str, str] = {}
        in_colors = False
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("//"):
                continue
            if line.startswith("@colors"):
                in_colors = True
                continue
            if in_colors and line.startswith("}"):
                in_colors = False
                continue
            if ":" in line and (in_colors or line.endswith(";")):
                key, value = line.split(":", 1)
                palette[key.strip().lower()] = value.strip().rstrip(";")
        return Theme(name=name, palette=palette)

    def _increment_version(self, message: str, *args: Any) -> None:
        """Increment internal version counter and emit a log message.

        Args:
            message (str): Log message template.
            *args (Any): Format arguments for the message.

        Returns:
            None
        """

        self._version += 1
        logger.debug(message, *args)


def get_theme_manager() -> ThemeManager:
    """Return the process-wide theme manager instance.

    Returns:
        ThemeManager: Global theme manager.
    """

    return ThemeManager()


def load_custom_theme(name: str, content: str | Path, *, activate: bool = False) -> Theme:
    """Load a custom theme from text or file path.

    Args:
        name (str): Theme identifier.
        content (str | Path): Theme definition or path to a file.
        activate (bool): Whether to activate the theme after loading.

    Returns:
        Theme: Loaded theme instance.
    """

    manager = get_theme_manager()
    if isinstance(content, Path) or Path(str(content)).exists():
        return manager.load_theme_file(Path(content), activate=activate)
    return manager.load_theme_text(name, str(content), activate=activate)


def set_theme(name: str) -> None:
    """Activate the theme named ``name``.

    Args:
        name (str): Registered theme name.

    Returns:
        None
    """

    get_theme_manager().set_active_theme(name)


def get_current_theme() -> Theme | None:
    """Return the currently active theme.

    Returns:
        Theme | None: Active theme instance or ``None`` when unset.
    """

    return get_theme_manager().get_active_theme()


def extend_theme(base_theme: str, overrides: Mapping[str, str], *, name: str | None = None) -> Theme:
    """Return a theme derived from ``base_theme`` with overrides applied.

    Args:
        base_theme (str): Existing theme name.
        overrides (Mapping[str, str]): Palette overrides to apply.
        name (str | None): Optional new theme name.

    Returns:
        Theme: Newly registered theme instance.
    """

    return get_theme_manager().extend_theme(base_theme, overrides, name=name)


__all__ = [
    "ThemeManager",
    "get_theme_manager",
    "load_custom_theme",
    "set_theme",
    "get_current_theme",
    "extend_theme",
]
