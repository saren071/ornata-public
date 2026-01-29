"""Auto-generated lazy exports for the rendering subsystem."""

from __future__ import annotations

from importlib import import_module

from ornata.api._warnings import setup_internal_warnings

setup_internal_warnings()

_EXPORT_TARGETS: dict[str, str] = {
    'gui': 'ornata.rendering.backends:gui',
    'tty': 'ornata.rendering.backends:tty',
    'ansi': 'ornata.rendering.backends.cli:ansi',
    'input': 'ornata.rendering.backends.cli:input',
    'platform': 'ornata.rendering.backends.cli:platform',
    'renderer': 'ornata.rendering.backends.cli:renderer',
    'session': 'ornata.rendering.backends.cli:session',
    'terminal': 'ornata.rendering.backends.cli:terminal',
    'terminal_app': 'ornata.rendering.backends.cli:terminal_app',
    'cursor': 'ornata.rendering.backends.cli.ansi:cursor',
    'palette': 'ornata.rendering.backends.cli.ansi:palette',
    'screen_buffer': 'ornata.rendering.backends.cli.ansi:screen_buffer',
    'sgr': 'ornata.rendering.backends.cli.ansi:sgr',
    'cursor_column': 'ornata.rendering.backends.cli.ansi.cursor:cursor_column',
    'cursor_get_position': 'ornata.rendering.backends.cli.ansi.cursor:cursor_get_position',
    'cursor_hide': 'ornata.rendering.backends.cli.ansi.cursor:cursor_hide',
    'cursor_move_down': 'ornata.rendering.backends.cli.ansi.cursor:cursor_move_down',
    'cursor_move_left': 'ornata.rendering.backends.cli.ansi.cursor:cursor_move_left',
    'cursor_move_right': 'ornata.rendering.backends.cli.ansi.cursor:cursor_move_right',
    'cursor_move_up': 'ornata.rendering.backends.cli.ansi.cursor:cursor_move_up',
    'cursor_next_line': 'ornata.rendering.backends.cli.ansi.cursor:cursor_next_line',
    'cursor_position': 'ornata.rendering.backends.cli.ansi.cursor:cursor_position',
    'cursor_position_from': 'ornata.rendering.backends.cli.ansi.cursor:cursor_position_from',
    'cursor_prev_line': 'ornata.rendering.backends.cli.ansi.cursor:cursor_prev_line',
    'cursor_restore_position': 'ornata.rendering.backends.cli.ansi.cursor:cursor_restore_position',
    'cursor_save_position': 'ornata.rendering.backends.cli.ansi.cursor:cursor_save_position',
    'cursor_scroll_down': 'ornata.rendering.backends.cli.ansi.cursor:cursor_scroll_down',
    'cursor_scroll_up': 'ornata.rendering.backends.cli.ansi.cursor:cursor_scroll_up',
    'cursor_set_style': 'ornata.rendering.backends.cli.ansi.cursor:cursor_set_style',
    'cursor_show': 'ornata.rendering.backends.cli.ansi.cursor:cursor_show',
    'parse_cursor_position_response': 'ornata.rendering.backends.cli.ansi.cursor:parse_cursor_position_response',
    'ansi_16_background': 'ornata.rendering.backends.cli.ansi.palette:ansi_16_background',
    'ansi_16_by_name': 'ornata.rendering.backends.cli.ansi.palette:ansi_16_by_name',
    'ansi_16_foreground': 'ornata.rendering.backends.cli.ansi.palette:ansi_16_foreground',
    'ansi_256_background': 'ornata.rendering.backends.cli.ansi.palette:ansi_256_background',
    'ansi_256_foreground': 'ornata.rendering.backends.cli.ansi.palette:ansi_256_foreground',
    'color_background': 'ornata.rendering.backends.cli.ansi.palette:color_background',
    'color_foreground': 'ornata.rendering.backends.cli.ansi.palette:color_foreground',
    'reset_background': 'ornata.rendering.backends.cli.ansi.palette:reset_background',
    'reset_colors': 'ornata.rendering.backends.cli.ansi.palette:reset_colors',
    'reset_foreground': 'ornata.rendering.backends.cli.ansi.palette:reset_foreground',
    'set_default_colors': 'ornata.rendering.backends.cli.ansi.palette:set_default_colors',
    'true_color_foreground': 'ornata.rendering.backends.cli.ansi.palette:true_color_foreground',
    'bell': 'ornata.rendering.backends.cli.ansi.screen_buffer:bell',
    'clear_line': 'ornata.rendering.backends.cli.ansi.screen_buffer:clear_line',
    'clear_line_from_cursor': 'ornata.rendering.backends.cli.ansi.screen_buffer:clear_line_from_cursor',
    'clear_line_to_cursor': 'ornata.rendering.backends.cli.ansi.screen_buffer:clear_line_to_cursor',
    'clear_screen': 'ornata.rendering.backends.cli.ansi.screen_buffer:clear_screen',
    'clear_screen_from_cursor': 'ornata.rendering.backends.cli.ansi.screen_buffer:clear_screen_from_cursor',
    'clear_screen_to_cursor': 'ornata.rendering.backends.cli.ansi.screen_buffer:clear_screen_to_cursor',
    'delete_chars': 'ornata.rendering.backends.cli.ansi.screen_buffer:delete_chars',
    'delete_lines': 'ornata.rendering.backends.cli.ansi.screen_buffer:delete_lines',
    'disable_alternate_screen_buffer': 'ornata.rendering.backends.cli.ansi.screen_buffer:disable_alternate_screen_buffer',
    'enable_alternate_screen_buffer': 'ornata.rendering.backends.cli.ansi.screen_buffer:enable_alternate_screen_buffer',
    'enter_alternate_buffer': 'ornata.rendering.backends.cli.ansi.screen_buffer:enter_alternate_buffer',
    'erase_in_display': 'ornata.rendering.backends.cli.ansi.screen_buffer:erase_in_display',
    'erase_in_line': 'ornata.rendering.backends.cli.ansi.screen_buffer:erase_in_line',
    'exit_alternate_buffer': 'ornata.rendering.backends.cli.ansi.screen_buffer:exit_alternate_buffer',
    'insert_chars': 'ornata.rendering.backends.cli.ansi.screen_buffer:insert_chars',
    'insert_lines': 'ornata.rendering.backends.cli.ansi.screen_buffer:insert_lines',
    'report_cursor_position': 'ornata.rendering.backends.cli.ansi.screen_buffer:report_cursor_position',
    'report_device_attributes': 'ornata.rendering.backends.cli.ansi.screen_buffer:report_device_attributes',
    'report_window_size': 'ornata.rendering.backends.cli.ansi.screen_buffer:report_window_size',
    'reset_scroll_region': 'ornata.rendering.backends.cli.ansi.screen_buffer:reset_scroll_region',
    'scroll_down': 'ornata.rendering.backends.cli.ansi.screen_buffer:scroll_down',
    'scroll_up': 'ornata.rendering.backends.cli.ansi.screen_buffer:scroll_up',
    'set_scroll_region': 'ornata.rendering.backends.cli.ansi.screen_buffer:set_scroll_region',
    'set_window_title': 'ornata.rendering.backends.cli.ansi.screen_buffer:set_window_title',
    'blink': 'ornata.rendering.backends.cli.ansi.sgr:blink',
    'bold': 'ornata.rendering.backends.cli.ansi.sgr:bold',
    'combine_styles': 'ornata.rendering.backends.cli.ansi.sgr:combine_styles',
    'dim': 'ornata.rendering.backends.cli.ansi.sgr:dim',
    'font_select': 'ornata.rendering.backends.cli.ansi.sgr:font_select',
    'fraktur': 'ornata.rendering.backends.cli.ansi.sgr:fraktur',
    'hidden': 'ornata.rendering.backends.cli.ansi.sgr:hidden',
    'italic': 'ornata.rendering.backends.cli.ansi.sgr:italic',
    'rapid_blink': 'ornata.rendering.backends.cli.ansi.sgr:rapid_blink',
    'reset_all': 'ornata.rendering.backends.cli.ansi.sgr:reset_all',
    'reset_blink': 'ornata.rendering.backends.cli.ansi.sgr:reset_blink',
    'reset_bold_dim': 'ornata.rendering.backends.cli.ansi.sgr:reset_bold_dim',
    'reset_hidden': 'ornata.rendering.backends.cli.ansi.sgr:reset_hidden',
    'reset_italic': 'ornata.rendering.backends.cli.ansi.sgr:reset_italic',
    'reset_reverse': 'ornata.rendering.backends.cli.ansi.sgr:reset_reverse',
    'reset_strikethrough': 'ornata.rendering.backends.cli.ansi.sgr:reset_strikethrough',
    'reset_underline': 'ornata.rendering.backends.cli.ansi.sgr:reset_underline',
    'reverse': 'ornata.rendering.backends.cli.ansi.sgr:reverse',
    'sgr_code': 'ornata.rendering.backends.cli.ansi.sgr:sgr_code',
    'sgr_codes': 'ornata.rendering.backends.cli.ansi.sgr:sgr_codes',
    'strikethrough': 'ornata.rendering.backends.cli.ansi.sgr:strikethrough',
    'style_from_text_style': 'ornata.rendering.backends.cli.ansi.sgr:style_from_text_style',
    'subscript': 'ornata.rendering.backends.cli.ansi.sgr:subscript',
    'superscript': 'ornata.rendering.backends.cli.ansi.sgr:superscript',
    'underline': 'ornata.rendering.backends.cli.ansi.sgr:underline',
    'underline_double': 'ornata.rendering.backends.cli.ansi.sgr:underline_double',
    'CLIInputPipeline': 'ornata.rendering.backends.cli.input:CLIInputPipeline',
    'create_cli_input_pipeline': 'ornata.rendering.backends.cli.input:create_cli_input_pipeline',
    'read_key': 'ornata.rendering.backends.cli.input:read_key',
    'conhost': 'ornata.rendering.backends.cli.platform:conhost',
    'detector': 'ornata.rendering.backends.cli.platform:detector',
    'ConHostAdapter': 'ornata.rendering.backends.cli.platform.conhost:ConHostAdapter',
    'detect_conhost_capabilities': 'ornata.rendering.backends.cli.platform.conhost:detect_conhost_capabilities',
    'get_conhost_adapter': 'ornata.rendering.backends.cli.platform.conhost:get_conhost_adapter',
    'is_conhost_available': 'ornata.rendering.backends.cli.platform.conhost:is_conhost_available',
    'detect_terminal_capabilities': 'ornata.rendering.backends.cli.platform.detector:detect_terminal_capabilities',
    'get_terminal_adapter': 'ornata.rendering.backends.cli.platform.detector:get_terminal_adapter',
    'ANSIRenderer': 'ornata.rendering.backends.cli.renderer:ANSIRenderer',
    'LiveSessionRenderer': 'ornata.rendering.backends.cli.session:LiveSessionRenderer',
    'TerminalRenderer': 'ornata.rendering.backends.cli.terminal:TerminalRenderer',
    'TerminalApp': 'ornata.rendering.backends.cli.terminal_app:TerminalApp',
    'TerminalSession': 'ornata.rendering.backends.cli.terminal_app:TerminalSession',
    'disable_mouse_reporting': 'ornata.rendering.backends.cli.terminal_app:disable_mouse_reporting',
    'enable_mouse_reporting': 'ornata.rendering.backends.cli.terminal_app:enable_mouse_reporting',
    'app': 'ornata.rendering.backends.gui:app',
    'contexts': 'ornata.rendering.backends.gui:contexts',
    'GuiApplication': 'ornata.rendering.backends.gui.app:GuiApplication',
    'create_application': 'ornata.rendering.backends.gui.app:create_application',
    'get_default_application': 'ornata.rendering.backends.gui.app:get_default_application',
    'Compositor': 'ornata.rendering.backends.gui.compositor:Compositor',
    'win32': 'ornata.rendering.backends.gui.platform:win32',
    'Win32EventHandler': 'ornata.rendering.backends.gui.platform.win32.events:Win32EventHandler',
    'Win32Window': 'ornata.rendering.backends.gui.platform.win32.window:Win32Window',
    'is_available': 'ornata.rendering.backends.gui.platform.win32.window:is_available',
    '_draw_box': 'ornata.rendering.backends.gui.renderer:_draw_box',
    '_draw_panel': 'ornata.rendering.backends.gui.renderer:_draw_panel',
    '_draw_text': 'ornata.rendering.backends.gui.renderer:_draw_text',
    '_render_node': 'ornata.rendering.backends.gui.renderer:_render_node',
    '_safe_fill_rect': 'ornata.rendering.backends.gui.renderer:_safe_fill_rect',
    'register': 'ornata.rendering.backends.gui.renderer:register',
    'render_tree': 'ornata.rendering.backends.gui.renderer:render_tree',
    'GuiRuntime': 'ornata.rendering.backends.gui.runtime:GuiRuntime',
    'GuiStream': 'ornata.rendering.backends.gui.runtime:GuiStream',
    'Surface': 'ornata.rendering.backends.gui.runtime:Surface',
    'get_runtime': 'ornata.rendering.backends.gui.runtime:get_runtime',
    'WindowRenderer': 'ornata.rendering.backends.gui.window:WindowRenderer',
    'termios': 'ornata.rendering.backends.tty:termios',
    'vt100': 'ornata.rendering.backends.tty:vt100',
    'InputReader': 'ornata.rendering.backends.tty.input:InputReader',
    'parse_mouse_event': 'ornata.rendering.backends.tty.input:parse_mouse_event',
    'bsd': 'ornata.rendering.backends.tty.platform:bsd',
    'TTYRenderer': 'ornata.rendering.backends.tty.renderer:TTYRenderer',
    'TerminalController': 'ornata.rendering.backends.tty.termios:TerminalController',
    'get_terminal_size': 'ornata.rendering.backends.tty.termios:get_terminal_size',
    'is_terminal': 'ornata.rendering.backends.tty.termios:is_terminal',
    'VT100': 'ornata.rendering.backends.tty.vt100:VT100',
    'EraseMode': 'ornata.rendering.backends.tty.vt100:EraseMode',
    'get_text_width': 'ornata.rendering.backends.tty.vt100:get_text_width',
    'base_renderer': 'ornata.rendering.core:base_renderer',
    'compositor': 'ornata.rendering.core:compositor',
    'frame': 'ornata.rendering.core:frame',
    'render_signals': 'ornata.rendering.core:render_signals',
    'RenderableBase': 'ornata.rendering.core.base_renderer:RenderableBase',
    'Renderer': 'ornata.rendering.core.base_renderer:Renderer',
    'get_capabilities': 'ornata.rendering.core.capabilities:get_capabilities',
    'get_cli_capabilities': 'ornata.rendering.core.capabilities:get_cli_capabilities',
    'get_gui_capabilities': 'ornata.rendering.core.capabilities:get_gui_capabilities',
    'get_tty_capabilities': 'ornata.rendering.core.capabilities:get_tty_capabilities',
    'FrameBuffer': 'ornata.rendering.core.frame:FrameBuffer',
    'RenderPipeline': 'ornata.rendering.core.pipeline:RenderPipeline',
    'SignalDispatcher': 'ornata.rendering.core.render_signals:SignalDispatcher',
    'SignalEmitter': 'ornata.rendering.core.render_signals:SignalEmitter',
    'get_global_dispatcher': 'ornata.rendering.core.render_signals:get_global_dispatcher',
    'get_global_emitter': 'ornata.rendering.core.render_signals:get_global_emitter',
    'VDOMAdapter': 'ornata.rendering.adapters.base:VDOMAdapter',
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
            "module 'ornata.api.exports.rendering' has no attribute {name!r}"
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
