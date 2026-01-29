"""Auto-generated exports for ornata.styling.language."""

from __future__ import annotations

from . import cascade, diag, engine, grammar

# from .ast import () Empty currently
from .cascade import (
    _apply_block,  # type: ignore [private]
    _handle_background,  # type: ignore [private]
    _handle_background_image,  # type: ignore [private]
    _handle_background_position,  # type: ignore [private]
    _handle_background_repeat,  # type: ignore [private]
    _handle_background_size,  # type: ignore [private]
    _handle_border,  # type: ignore [private]
    _handle_border_color,  # type: ignore [private]
    _handle_border_radius,  # type: ignore [private]
    _handle_box_shadow,  # type: ignore [private]
    _handle_color,  # type: ignore [private]
    _handle_component_extra,  # type: ignore [private]
    _handle_font,  # type: ignore [private]
    _handle_font_size,  # type: ignore [private]
    _handle_font_weight,  # type: ignore [private]
    _handle_height,  # type: ignore [private]
    _handle_letter_spacing,  # type: ignore [private]
    _handle_line_height,  # type: ignore [private]
    _handle_margin,  # type: ignore [private]
    _handle_opacity,  # type: ignore [private]
    _handle_outline,  # type: ignore [private]
    _handle_padding,  # type: ignore [private]
    _handle_text_align,  # type: ignore [private]
    _handle_text_decoration,  # type: ignore [private]
    _handle_text_transform,  # type: ignore [private]
    _handle_transform,  # type: ignore [private]
    _handle_width,  # type: ignore [private]
    _handle_word_spacing,  # type: ignore [private]
    _matches_component,  # type: ignore [private]
    _resolve_color,  # type: ignore [private]
    _split_tokens,  # type: ignore [private]
    resolve_stylesheet,
)
from .diag import (
    clear,
    error,
    last_errors,
    last_warnings,
    warn,
)
from .engine import (
    StyleEngine,
    _caps_signature,  # type: ignore [private]
    _extract_component_name,  # type: ignore [private]
    _merge_styles,  # type: ignore [private]
    _safe_call,  # type: ignore [private]
)
from .grammar import (
    _Parser,  # type: ignore [private]
    parse_stylesheet,
)

# from .values import () Empty currently

__all__ = [
    "StyleEngine",
    "_Parser",
    "_apply_block",
    "_caps_signature",
    "_extract_component_name",
    "_handle_background",
    "_handle_background_image",
    "_handle_background_position",
    "_handle_background_repeat",
    "_handle_background_size",
    "_handle_border",
    "_handle_border_color",
    "_handle_border_radius",
    "_handle_box_shadow",
    "_handle_color",
    "_handle_component_extra",
    "_handle_font",
    "_handle_font_size",
    "_handle_font_weight",
    "_handle_height",
    "_handle_letter_spacing",
    "_handle_line_height",
    "_handle_margin",
    "_handle_opacity",
    "_handle_outline",
    "_handle_padding",
    "_handle_text_align",
    "_handle_text_decoration",
    "_handle_text_transform",
    "_handle_transform",
    "_handle_width",
    "_handle_word_spacing",
    "_matches_component",
    "_merge_styles",
    "_resolve_color",
    "_safe_call",
    "_split_tokens",
    "clear",
    "error",
    "last_errors",
    "last_warnings",
    "parse_stylesheet",
    "resolve_stylesheet",
    "cascade",
    "diag",
    "engine",
    "grammar",
    "warn",
]
