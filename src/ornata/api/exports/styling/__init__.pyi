"""Type stubs for the styling subsystem exports."""

from __future__ import annotations

from ornata.styling import colorkit as colorkit
from ornata.styling import colors as colors
from ornata.styling import integration_service as integration_service
from ornata.styling import language as language
from ornata.styling import runtime as runtime
from ornata.styling import theming as theming
from ornata.styling import validators as validators
from ornata.styling.adapters import cli_mapper as cli_mapper
from ornata.styling.adapters import gui_mapper as gui_mapper
from ornata.styling.adapters import tty_mapper as tty_mapper
from ornata.styling.adapters.cli_mapper import CLIMapper as CLIMapper
from ornata.styling.adapters.gui_mapper import GUIMapper as GUIMapper
from ornata.styling.adapters.tty_mapper import TTYMapper as TTYMapper
from ornata.styling.colorkit import contrast as contrast
from ornata.styling.colorkit import gradients as gradients
from ornata.styling.colorkit import resolver as resolver
from ornata.styling.colorkit import spaces as spaces
from ornata.styling.colorkit import vision as vision
from ornata.styling.colorkit.ansi import AnsiConverter as AnsiConverter
from ornata.styling.colorkit.contrast import ContrastAnalyzer as ContrastAnalyzer
from ornata.styling.colorkit.gradients import GradientRenderer as GradientRenderer
from ornata.styling.colorkit.gradients import render_gradient as render_gradient
from ornata.styling.colorkit.palette import PaletteEntry as PaletteEntry
from ornata.styling.colorkit.palette import PaletteLibrary as PaletteLibrary
from ornata.styling.colorkit.resolver import BoundedCache as BoundedCache
from ornata.styling.colorkit.resolver import ColorResolver as ColorResolver
from ornata.styling.colorkit.spaces import ColorSpaces as ColorSpaces
from ornata.styling.colorkit.vision import ColorVisionSimulator as ColorVisionSimulator
from ornata.styling.colors import Color as Color
from ornata.styling.colors import _theme_lookup as _theme_lookup  # type: ignore
from ornata.styling.colors import _theme_version as _theme_version  # type: ignore
from ornata.styling.colors import resolve_rgb as resolve_rgb
from ornata.styling.integration_service import StylingIntegrationService as StylingIntegrationService
from ornata.styling.integration_service import resolve_color as resolve_color
from ornata.styling.language import cascade as cascade
from ornata.styling.language import diag as diag
from ornata.styling.language import engine as engine
from ornata.styling.language import grammar as grammar
from ornata.styling.language.cascade import _apply_block as _apply_block  # type: ignore
from ornata.styling.language.cascade import _handle_background as _handle_background  # type: ignore
from ornata.styling.language.cascade import _handle_background_image as _handle_background_image  # type: ignore
from ornata.styling.language.cascade import _handle_background_position as _handle_background_position  # type: ignore
from ornata.styling.language.cascade import _handle_background_repeat as _handle_background_repeat  # type: ignore
from ornata.styling.language.cascade import _handle_background_size as _handle_background_size  # type: ignore
from ornata.styling.language.cascade import _handle_border as _handle_border  # type: ignore
from ornata.styling.language.cascade import _handle_border_color as _handle_border_color  # type: ignore
from ornata.styling.language.cascade import _handle_border_radius as _handle_border_radius  # type: ignore
from ornata.styling.language.cascade import _handle_box_shadow as _handle_box_shadow  # type: ignore
from ornata.styling.language.cascade import _handle_color as _handle_color  # type: ignore
from ornata.styling.language.cascade import _handle_component_extra as _handle_component_extra  # type: ignore
from ornata.styling.language.cascade import _handle_font as _handle_font  # type: ignore
from ornata.styling.language.cascade import _handle_font_size as _handle_font_size  # type: ignore
from ornata.styling.language.cascade import _handle_font_weight as _handle_font_weight  # type: ignore
from ornata.styling.language.cascade import _handle_height as _handle_height  # type: ignore
from ornata.styling.language.cascade import _handle_letter_spacing as _handle_letter_spacing  # type: ignore
from ornata.styling.language.cascade import _handle_line_height as _handle_line_height  # type: ignore
from ornata.styling.language.cascade import _handle_margin as _handle_margin  # type: ignore
from ornata.styling.language.cascade import _handle_opacity as _handle_opacity  # type: ignore
from ornata.styling.language.cascade import _handle_outline as _handle_outline  # type: ignore
from ornata.styling.language.cascade import _handle_padding as _handle_padding  # type: ignore
from ornata.styling.language.cascade import _handle_text_align as _handle_text_align  # type: ignore
from ornata.styling.language.cascade import _handle_text_decoration as _handle_text_decoration  # type: ignore
from ornata.styling.language.cascade import _handle_text_transform as _handle_text_transform  # type: ignore
from ornata.styling.language.cascade import _handle_transform as _handle_transform  # type: ignore
from ornata.styling.language.cascade import _handle_width as _handle_width  # type: ignore
from ornata.styling.language.cascade import _handle_word_spacing as _handle_word_spacing  # type: ignore
from ornata.styling.language.cascade import _matches_component as _matches_component  # type: ignore
from ornata.styling.language.cascade import _resolve_color as _resolve_color  # type: ignore
from ornata.styling.language.cascade import _split_tokens as _split_tokens  # type: ignore
from ornata.styling.language.cascade import resolve_stylesheet as resolve_stylesheet
from ornata.styling.language.diag import clear as clear
from ornata.styling.language.diag import error as error
from ornata.styling.language.diag import last_errors as last_errors
from ornata.styling.language.diag import last_warnings as last_warnings
from ornata.styling.language.diag import warn as warn
from ornata.styling.language.engine import StyleEngine as StyleEngine
from ornata.styling.language.engine import _caps_signature as _caps_signature  # type: ignore
from ornata.styling.language.engine import _extract_component_name as _extract_component_name  # type: ignore
from ornata.styling.language.engine import _merge_styles as _merge_styles  # type: ignore
from ornata.styling.language.engine import _safe_call as _safe_call  # type: ignore
from ornata.styling.language.grammar import _Parser as _Parser  # type: ignore
from ornata.styling.language.grammar import parse_stylesheet as parse_stylesheet
from ornata.styling.runtime import borders as borders
from ornata.styling.runtime import typography as typography
from ornata.styling.runtime.borders import StylingBorders as StylingBorders
from ornata.styling.runtime.runtime import StylingContext as StylingContext
from ornata.styling.runtime.runtime import StylingRuntime as StylingRuntime
from ornata.styling.runtime.runtime import get_styling_runtime as get_styling_runtime
from ornata.styling.runtime.runtime import resolve_component_style as resolve_component_style
from ornata.styling.runtime.typography import TypographyEngine as TypographyEngine
from ornata.styling.services import get_style_engine as get_style_engine
from ornata.styling.theming import manager as manager
from ornata.styling.theming import registry as registry
from ornata.styling.theming.manager import ThemeManager as ThemeManager
from ornata.styling.theming.manager import extend_theme as extend_theme
from ornata.styling.theming.manager import get_current_theme as get_current_theme
from ornata.styling.theming.manager import get_theme_manager as get_theme_manager
from ornata.styling.theming.manager import load_custom_theme as load_custom_theme
from ornata.styling.theming.manager import set_theme as set_theme
from ornata.styling.theming.registry import StylingRegistry as StylingRegistry
from ornata.styling.validators import StyleValidator as StyleValidator
from ornata.styling.validators import ValidationError as ValidationError
from ornata.styling.validators import _style_to_dict as _style_to_dict  # type: ignore

__all__ = [
    "AnsiConverter",
    "BoundedCache",
    "CLIMapper",
    "ColorResolver",
    "ColorSpaces",
    "ColorVisionSimulator",
    "ContrastAnalyzer",
    "GUIMapper",
    "GradientRenderer",
    "PaletteEntry",
    "PaletteLibrary",
    "StyleEngine",
    "StyleValidator",
    "StylingContext",
    "StylingBorders",
    "StylingRegistry",
    "StylingRuntime",
    "TTYMapper",
    "ThemeManager",
    "TypographyEngine",
    "ValidationError",
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
    "_style_to_dict",
    "_theme_lookup",
    "_theme_version",
    "clear",
    "cli_mapper",
    "colorkit",
    "colors",
    "contrast",
    "error",
    "extend_theme",
    "get_current_theme",
    "get_style_engine",
    "get_styling_runtime",
    "get_theme_manager",
    "gradients",
    "gui_mapper",
    "language",
    "last_errors",
    "last_warnings",
    "load_custom_theme",
    "parse_stylesheet",
    "resolve_component_style",
    "resolve_stylesheet",
    "resolver",
    "runtime",
    "set_theme",
    "spaces",
    "borders",
    "cascade",
    "diag",
    "engine",
    "grammar",
    "manager",
    "registry",
    "runtime",
    "typography",
    "validators",
    "theming",
    "tty_mapper",
    "vision",
    "warn",
    "resolve_rgb",
    "render_gradient",
    "Color",
    "StylingIntegrationService",
    "resolve_color",
    "integration_service",
]