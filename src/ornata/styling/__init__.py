"""Auto-generated exports for ornata.styling."""

from __future__ import annotations

from . import adapters, colorkit, colors, integration_service, language, runtime, services, theming, validators
from .colors import (
    Color,
    _theme_lookup,  # type: ignore [private]
    _theme_version,  # type: ignore [private]
    resolve_rgb,
)
from .integration_service import StylingIntegrationService, resolve_color
from .services import get_style_engine
from .validators import (
    StyleValidator,
    _style_to_dict,  # type: ignore [private]
)

__all__ = [
    "Color",
    "StyleValidator",
    "_style_to_dict",
    "_theme_lookup",
    "_theme_version",
    "adapters",
    "colorkit",
    "colors",
    "get_style_engine",
    "language",
    "runtime",
    "services",
    "validators",
    "theming",
    "resolve_color",
    "integration_service",
    "resolve_rgb",
    "StylingIntegrationService",
]
