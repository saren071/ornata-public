"""Auto-generated lazy exports for the styling subsystem."""

from __future__ import annotations

from importlib import import_module

from ornata.api._warnings import setup_internal_warnings

setup_internal_warnings()

_EXPORT_TARGETS: dict[str, str] = {
    'colorkit': 'ornata.styling:colorkit',
    'colors': 'ornata.styling:colors',
    'language': 'ornata.styling:language',
    'runtime': 'ornata.styling:runtime',
    'theming': 'ornata.styling:theming',
    'validators': 'ornata.styling:validators',
    'adapters': 'ornata.styling:adapters',
    'cli_mapper': 'ornata.styling.adapters:cli_mapper',
    'gui_mapper': 'ornata.styling.adapters:gui_mapper',
    'tty_mapper': 'ornata.styling.adapters:tty_mapper',
    'CLIMapper': 'ornata.styling.adapters:CLIMapper',
    'GUIMapper': 'ornata.styling.adapters:GUIMapper',
    'TTYMapper': 'ornata.styling.adapters:TTYMapper',
    'contrast': 'ornata.styling.colorkit:contrast',
    'gradients': 'ornata.styling.colorkit:gradients',
    'resolver': 'ornata.styling.colorkit:resolver',
    'spaces': 'ornata.styling.colorkit:spaces',
    'vision': 'ornata.styling.colorkit:vision',
    'AnsiConverter': 'ornata.styling.colorkit.ansi:AnsiConverter',
    'ContrastAnalyzer': 'ornata.styling.colorkit.contrast:ContrastAnalyzer',
    'GradientRenderer': 'ornata.styling.colorkit.gradients:GradientRenderer',
    'render_gradient': 'ornata.styling.colorkit.gradients:render_gradient',
    'PaletteLibrary': 'ornata.styling.colorkit.palette:PaletteLibrary',
    'BoundedCache': 'ornata.styling.colorkit.resolver:BoundedCache',
    'ColorResolver': 'ornata.styling.colorkit.resolver:ColorResolver',
    'ColorSpaces': 'ornata.styling.colorkit.spaces:ColorSpaces',
    'ColorVisionSimulator': 'ornata.styling.colorkit.vision:ColorVisionSimulator',
    'Color': 'ornata.styling.colors:Color',
    '_theme_lookup': 'ornata.styling.colors:_theme_lookup',
    '_theme_version': 'ornata.styling.colors:_theme_version',
    'resolve_rgb': 'ornata.styling.colors:resolve_rgb',
    'cascade': 'ornata.styling.language:cascade',
    'diag': 'ornata.styling.language:diag',
    'engine': 'ornata.styling.language:engine',
    'grammar': 'ornata.styling.language:grammar',
    '_apply_block': 'ornata.styling.language.cascade:_apply_block',
    '_handle_background': 'ornata.styling.language.cascade:_handle_background',
    '_handle_background_image': 'ornata.styling.language.cascade:_handle_background_image',
    '_handle_background_position': 'ornata.styling.language.cascade:_handle_background_position',
    '_handle_background_repeat': 'ornata.styling.language.cascade:_handle_background_repeat',
    '_handle_background_size': 'ornata.styling.language.cascade:_handle_background_size',
    '_handle_border': 'ornata.styling.language.cascade:_handle_border',
    '_handle_border_color': 'ornata.styling.language.cascade:_handle_border_color',
    '_handle_border_radius': 'ornata.styling.language.cascade:_handle_border_radius',
    '_handle_box_shadow': 'ornata.styling.language.cascade:_handle_box_shadow',
    '_handle_color': 'ornata.styling.language.cascade:_handle_color',
    '_handle_component_extra': 'ornata.styling.language.cascade:_handle_component_extra',
    '_handle_font': 'ornata.styling.language.cascade:_handle_font',
    '_handle_font_size': 'ornata.styling.language.cascade:_handle_font_size',
    '_handle_font_weight': 'ornata.styling.language.cascade:_handle_font_weight',
    '_handle_height': 'ornata.styling.language.cascade:_handle_height',
    '_handle_letter_spacing': 'ornata.styling.language.cascade:_handle_letter_spacing',
    '_handle_line_height': 'ornata.styling.language.cascade:_handle_line_height',
    '_handle_margin': 'ornata.styling.language.cascade:_handle_margin',
    '_handle_opacity': 'ornata.styling.language.cascade:_handle_opacity',
    '_handle_outline': 'ornata.styling.language.cascade:_handle_outline',
    '_handle_padding': 'ornata.styling.language.cascade:_handle_padding',
    '_handle_text_align': 'ornata.styling.language.cascade:_handle_text_align',
    '_handle_text_decoration': 'ornata.styling.language.cascade:_handle_text_decoration',
    '_handle_text_transform': 'ornata.styling.language.cascade:_handle_text_transform',
    '_handle_transform': 'ornata.styling.language.cascade:_handle_transform',
    '_handle_width': 'ornata.styling.language.cascade:_handle_width',
    '_handle_word_spacing': 'ornata.styling.language.cascade:_handle_word_spacing',
    '_matches_component': 'ornata.styling.language.cascade:_matches_component',
    '_resolve_color': 'ornata.styling.language.cascade:_resolve_color',
    '_split_tokens': 'ornata.styling.language.cascade:_split_tokens',
    'resolve_stylesheet': 'ornata.styling.language.cascade:resolve_stylesheet',
    'clear': 'ornata.styling.language.diag:clear',
    'error': 'ornata.styling.language.diag:error',
    'last_errors': 'ornata.styling.language.diag:last_errors',
    'last_warnings': 'ornata.styling.language.diag:last_warnings',
    'warn': 'ornata.styling.language.diag:warn',
    'StyleEngine': 'ornata.styling.language.engine:StyleEngine',
    '_caps_signature': 'ornata.styling.language.engine:_caps_signature',
    '_extract_component_name': 'ornata.styling.language.engine:_extract_component_name',
    '_merge_styles': 'ornata.styling.language.engine:_merge_styles',
    '_safe_call': 'ornata.styling.language.engine:_safe_call',
    'parse_stylesheet': 'ornata.styling.language.grammar:parse_stylesheet',
    'borders': 'ornata.styling.runtime:borders',
    'typography': 'ornata.styling.runtime:typography',
    'StylingBorders': 'ornata.styling.runtime.borders:StylingBorders',
    'StylingRuntime': 'ornata.styling.runtime.runtime:StylingRuntime',
    'get_styling_runtime': 'ornata.styling.runtime.runtime:get_styling_runtime',
    'resolve_component_style': 'ornata.styling.runtime.runtime:resolve_component_style',
    'TypographyEngine': 'ornata.styling.runtime.typography:TypographyEngine',
    'get_style_engine': 'ornata.styling.services:get_style_engine',
    'manager': 'ornata.styling.theming:manager',
    'registry': 'ornata.styling.theming:registry',
    'ThemeManager': 'ornata.styling.theming.manager:ThemeManager',
    'extend_theme': 'ornata.styling.theming.manager:extend_theme',
    'get_current_theme': 'ornata.styling.theming.manager:get_current_theme',
    'get_theme_manager': 'ornata.styling.theming.manager:get_theme_manager',
    'load_custom_theme': 'ornata.styling.theming.manager:load_custom_theme',
    'set_theme': 'ornata.styling.theming.manager:set_theme',
    'StylingRegistry': 'ornata.styling.theming.registry:StylingRegistry',
    'StyleValidator': 'ornata.styling.validators:StyleValidator',
    '_style_to_dict': 'ornata.styling.validators:_style_to_dict',
    'StylingIntegrationService': 'ornata.styling.integration_service:StylingIntegrationService',
    'resolve_color': 'ornata.styling.integration_service:resolve_color',
    'integration_service': 'ornata.styling:integration_service',
}

_RESOLVED_EXPORTS: dict[str, object] = {}

__all__ = ["__getattr__"]

def _load_target(name: str) -> object:
    """Load and cache ``name`` for this subsystem.

    Parameters
    ----------
    name : str
        Export name to resolve.

    Returns
    -------
    object
        Resolved attribute from the owning module.

    Raises
    ------
    AttributeError
        If ``name`` is unknown to this subsystem.
    """

    target = _EXPORT_TARGETS.get(name)
    if target is None:
        raise AttributeError(
            "module 'ornata.api.exports.styling' has no attribute {name!r}"
        )
    module_name, _, attr_name = target.partition(':')
    module = import_module(module_name)
    value = getattr(module, attr_name)
    _RESOLVED_EXPORTS[name] = value
    globals()[name] = value
    return value

def __getattr__(name: str) -> object:
    """Resolve an export attribute on first access.

    Parameters
    ----------
    name : str
        Export name requested from this module.

    Returns
    -------
    object
        Resolved export value.

    Raises
    ------
    AttributeError
        If ``name`` is not part of this subsystem.
    """

    if name in _RESOLVED_EXPORTS:
        return _RESOLVED_EXPORTS[name]
    return _load_target(name)

def __dir__() -> list[str]:
    """Return the sorted list of exportable names.

    Returns
    -------
    list[str]
        Sorted names available via this module.
    """

    names = ['__getattr__']
    names.extend(_EXPORT_TARGETS)
    return sorted(names)
