"""Type stubs for the rendering subsystem exports."""

from __future__ import annotations

from ornata.rendering.adapters import VDOMAdapter
from ornata.rendering.backends import gui as gui
from ornata.rendering.backends import tty as tty
from ornata.rendering.backends.cli import ansi as ansi
from ornata.rendering.backends.cli import input as input
from ornata.rendering.backends.cli import platform as platform
from ornata.rendering.backends.cli import renderer as renderer
from ornata.rendering.backends.cli import session as session
from ornata.rendering.backends.cli import terminal as terminal
from ornata.rendering.backends.cli import terminal_app as terminal_app
from ornata.rendering.backends.cli.ansi import cursor as cursor
from ornata.rendering.backends.cli.ansi import palette as palette
from ornata.rendering.backends.cli.ansi import screen_buffer as screen_buffer
from ornata.rendering.backends.cli.ansi import sgr as sgr
from ornata.rendering.backends.cli.ansi.cursor import cursor_column as cursor_column
from ornata.rendering.backends.cli.ansi.cursor import cursor_get_position as cursor_get_position
from ornata.rendering.backends.cli.ansi.cursor import cursor_hide as cursor_hide
from ornata.rendering.backends.cli.ansi.cursor import cursor_move_down as cursor_move_down
from ornata.rendering.backends.cli.ansi.cursor import cursor_move_left as cursor_move_left
from ornata.rendering.backends.cli.ansi.cursor import cursor_move_right as cursor_move_right
from ornata.rendering.backends.cli.ansi.cursor import cursor_move_up as cursor_move_up
from ornata.rendering.backends.cli.ansi.cursor import cursor_next_line as cursor_next_line
from ornata.rendering.backends.cli.ansi.cursor import cursor_position as cursor_position
from ornata.rendering.backends.cli.ansi.cursor import cursor_position_from as cursor_position_from
from ornata.rendering.backends.cli.ansi.cursor import cursor_prev_line as cursor_prev_line
from ornata.rendering.backends.cli.ansi.cursor import cursor_restore_position as cursor_restore_position
from ornata.rendering.backends.cli.ansi.cursor import cursor_save_position as cursor_save_position
from ornata.rendering.backends.cli.ansi.cursor import cursor_scroll_down as cursor_scroll_down
from ornata.rendering.backends.cli.ansi.cursor import cursor_scroll_up as cursor_scroll_up
from ornata.rendering.backends.cli.ansi.cursor import cursor_set_style as cursor_set_style
from ornata.rendering.backends.cli.ansi.cursor import cursor_show as cursor_show
from ornata.rendering.backends.cli.ansi.cursor import parse_cursor_position_response as parse_cursor_position_response
from ornata.rendering.backends.cli.ansi.palette import ansi_16_background as ansi_16_background
from ornata.rendering.backends.cli.ansi.palette import ansi_16_by_name as ansi_16_by_name
from ornata.rendering.backends.cli.ansi.palette import ansi_16_foreground as ansi_16_foreground
from ornata.rendering.backends.cli.ansi.palette import ansi_256_background as ansi_256_background
from ornata.rendering.backends.cli.ansi.palette import ansi_256_foreground as ansi_256_foreground
from ornata.rendering.backends.cli.ansi.palette import color_background as color_background
from ornata.rendering.backends.cli.ansi.palette import color_foreground as color_foreground
from ornata.rendering.backends.cli.ansi.palette import reset_background as reset_background
from ornata.rendering.backends.cli.ansi.palette import reset_colors as reset_colors
from ornata.rendering.backends.cli.ansi.palette import reset_foreground as reset_foreground
from ornata.rendering.backends.cli.ansi.palette import set_default_colors as set_default_colors
from ornata.rendering.backends.cli.ansi.palette import true_color_foreground as true_color_foreground
from ornata.rendering.backends.cli.ansi.screen_buffer import bell as bell
from ornata.rendering.backends.cli.ansi.screen_buffer import clear_line as clear_line
from ornata.rendering.backends.cli.ansi.screen_buffer import clear_line_from_cursor as clear_line_from_cursor
from ornata.rendering.backends.cli.ansi.screen_buffer import clear_line_to_cursor as clear_line_to_cursor
from ornata.rendering.backends.cli.ansi.screen_buffer import clear_screen as clear_screen
from ornata.rendering.backends.cli.ansi.screen_buffer import clear_screen_from_cursor as clear_screen_from_cursor
from ornata.rendering.backends.cli.ansi.screen_buffer import clear_screen_to_cursor as clear_screen_to_cursor
from ornata.rendering.backends.cli.ansi.screen_buffer import delete_chars as delete_chars
from ornata.rendering.backends.cli.ansi.screen_buffer import delete_lines as delete_lines
from ornata.rendering.backends.cli.ansi.screen_buffer import disable_alternate_screen_buffer as disable_alternate_screen_buffer
from ornata.rendering.backends.cli.ansi.screen_buffer import enable_alternate_screen_buffer as enable_alternate_screen_buffer
from ornata.rendering.backends.cli.ansi.screen_buffer import enter_alternate_buffer as enter_alternate_buffer
from ornata.rendering.backends.cli.ansi.screen_buffer import erase_in_display as erase_in_display
from ornata.rendering.backends.cli.ansi.screen_buffer import erase_in_line as erase_in_line
from ornata.rendering.backends.cli.ansi.screen_buffer import exit_alternate_buffer as exit_alternate_buffer
from ornata.rendering.backends.cli.ansi.screen_buffer import insert_chars as insert_chars
from ornata.rendering.backends.cli.ansi.screen_buffer import insert_lines as insert_lines
from ornata.rendering.backends.cli.ansi.screen_buffer import report_cursor_position as report_cursor_position
from ornata.rendering.backends.cli.ansi.screen_buffer import report_device_attributes as report_device_attributes
from ornata.rendering.backends.cli.ansi.screen_buffer import report_window_size as report_window_size
from ornata.rendering.backends.cli.ansi.screen_buffer import reset_scroll_region as reset_scroll_region
from ornata.rendering.backends.cli.ansi.screen_buffer import scroll_down as scroll_down
from ornata.rendering.backends.cli.ansi.screen_buffer import scroll_up as scroll_up
from ornata.rendering.backends.cli.ansi.screen_buffer import set_scroll_region as set_scroll_region
from ornata.rendering.backends.cli.ansi.screen_buffer import set_window_title as set_window_title
from ornata.rendering.backends.cli.ansi.sgr import blink as blink
from ornata.rendering.backends.cli.ansi.sgr import bold as bold
from ornata.rendering.backends.cli.ansi.sgr import combine_styles as combine_styles
from ornata.rendering.backends.cli.ansi.sgr import dim as dim
from ornata.rendering.backends.cli.ansi.sgr import font_select as font_select
from ornata.rendering.backends.cli.ansi.sgr import fraktur as fraktur
from ornata.rendering.backends.cli.ansi.sgr import hidden as hidden
from ornata.rendering.backends.cli.ansi.sgr import italic as italic
from ornata.rendering.backends.cli.ansi.sgr import rapid_blink as rapid_blink
from ornata.rendering.backends.cli.ansi.sgr import reset_all as reset_all
from ornata.rendering.backends.cli.ansi.sgr import reset_blink as reset_blink
from ornata.rendering.backends.cli.ansi.sgr import reset_bold_dim as reset_bold_dim
from ornata.rendering.backends.cli.ansi.sgr import reset_hidden as reset_hidden
from ornata.rendering.backends.cli.ansi.sgr import reset_italic as reset_italic
from ornata.rendering.backends.cli.ansi.sgr import reset_reverse as reset_reverse
from ornata.rendering.backends.cli.ansi.sgr import reset_strikethrough as reset_strikethrough
from ornata.rendering.backends.cli.ansi.sgr import reset_underline as reset_underline
from ornata.rendering.backends.cli.ansi.sgr import reverse as reverse
from ornata.rendering.backends.cli.ansi.sgr import sgr_code as sgr_code
from ornata.rendering.backends.cli.ansi.sgr import sgr_codes as sgr_codes
from ornata.rendering.backends.cli.ansi.sgr import strikethrough as strikethrough
from ornata.rendering.backends.cli.ansi.sgr import style_from_text_style as style_from_text_style
from ornata.rendering.backends.cli.ansi.sgr import subscript as subscript
from ornata.rendering.backends.cli.ansi.sgr import superscript as superscript
from ornata.rendering.backends.cli.ansi.sgr import underline as underline
from ornata.rendering.backends.cli.ansi.sgr import underline_double as underline_double
from ornata.rendering.backends.cli.input import CLIInputPipeline as CLIInputPipeline
from ornata.rendering.backends.cli.input import create_cli_input_pipeline as create_cli_input_pipeline
from ornata.rendering.backends.cli.input import read_key as read_key
from ornata.rendering.backends.cli.platform import conhost as conhost
from ornata.rendering.backends.cli.platform import detector as detector
from ornata.rendering.backends.cli.platform.conhost import ConHostAdapter as ConHostAdapter
from ornata.rendering.backends.cli.platform.conhost import detect_conhost_capabilities as detect_conhost_capabilities
from ornata.rendering.backends.cli.platform.conhost import get_conhost_adapter as get_conhost_adapter
from ornata.rendering.backends.cli.platform.conhost import is_conhost_available as is_conhost_available
from ornata.rendering.backends.cli.platform.detector import detect_terminal_capabilities as detect_terminal_capabilities
from ornata.rendering.backends.cli.platform.detector import get_terminal_adapter as get_terminal_adapter
from ornata.rendering.backends.cli.renderer import ANSIRenderer as ANSIRenderer
from ornata.rendering.backends.cli.session import LiveSessionRenderer as LiveSessionRenderer
from ornata.rendering.backends.cli.terminal import TerminalRenderer as TerminalRenderer
from ornata.rendering.backends.cli.terminal_app import TerminalApp as TerminalApp
from ornata.rendering.backends.cli.terminal_app import TerminalSession as TerminalSession
from ornata.rendering.backends.cli.terminal_app import disable_mouse_reporting as disable_mouse_reporting
from ornata.rendering.backends.cli.terminal_app import enable_mouse_reporting as enable_mouse_reporting
from ornata.rendering.backends.gui import app as app
from ornata.rendering.backends.gui import contexts as contexts
from ornata.rendering.backends.gui.app import GuiApplication as GuiApplication
from ornata.rendering.backends.gui.app import create_application as create_application
from ornata.rendering.backends.gui.app import get_default_application as get_default_application
from ornata.rendering.backends.gui.compositor import Compositor as Compositor
from ornata.rendering.backends.gui.platform import win32 as win32
from ornata.rendering.backends.gui.platform.win32.events import Win32EventHandler as Win32EventHandler
from ornata.rendering.backends.gui.platform.win32.window import Win32Window as Win32Window
from ornata.rendering.backends.gui.platform.win32.window import is_available as is_available
from ornata.rendering.backends.gui.renderer import GuiNodeLike as GuiNodeLike
from ornata.rendering.backends.gui.renderer import _draw_box as _draw_box  # type: ignore
from ornata.rendering.backends.gui.renderer import _draw_panel as _draw_panel  # type: ignore
from ornata.rendering.backends.gui.renderer import _draw_text as _draw_text  # type: ignore
from ornata.rendering.backends.gui.renderer import _render_node as _render_node  # type: ignore
from ornata.rendering.backends.gui.renderer import _safe_fill_rect as _safe_fill_rect  # type: ignore
from ornata.rendering.backends.gui.renderer import register as register
from ornata.rendering.backends.gui.renderer import render_tree as render_tree
from ornata.rendering.backends.gui.runtime import GuiRuntime as GuiRuntime
from ornata.rendering.backends.gui.runtime import GuiStream as GuiStream
from ornata.rendering.backends.gui.runtime import Surface as Surface
from ornata.rendering.backends.gui.runtime import get_runtime as get_runtime
from ornata.rendering.backends.gui.window import WindowRenderer as WindowRenderer
from ornata.rendering.backends.tty import termios as termios
from ornata.rendering.backends.tty import vt100 as vt100
from ornata.rendering.backends.tty.input import InputReader as InputReader
from ornata.rendering.backends.tty.input import KeyEvent as KeyEvent
from ornata.rendering.backends.tty.input import MouseEvent as MouseEvent
from ornata.rendering.backends.tty.input import parse_mouse_event as parse_mouse_event
from ornata.rendering.backends.tty.platform import bsd as bsd
from ornata.rendering.backends.tty.renderer import TTYRenderer as TTYRenderer
from ornata.rendering.backends.tty.termios import TerminalController as TerminalController
from ornata.rendering.backends.tty.termios import TerminalState as TerminalState
from ornata.rendering.backends.tty.termios import get_terminal_size as get_terminal_size
from ornata.rendering.backends.tty.termios import is_terminal as is_terminal
from ornata.rendering.backends.tty.vt100 import VT100 as VT100
from ornata.rendering.backends.tty.vt100 import Color8 as Color8
from ornata.rendering.backends.tty.vt100 import EraseMode as EraseMode
from ornata.rendering.backends.tty.vt100 import get_text_width as get_text_width
from ornata.rendering.core import base_renderer as base_renderer
from ornata.rendering.core import compositor as compositor
from ornata.rendering.core import frame as frame
from ornata.rendering.core import render_signals as render_signals
from ornata.rendering.core.base_renderer import RenderableBase as RenderableBase
from ornata.rendering.core.base_renderer import Renderer as Renderer
from ornata.rendering.core.capabilities import RendererCapabilities as RendererCapabilities
from ornata.rendering.core.capabilities import get_capabilities as get_capabilities
from ornata.rendering.core.capabilities import get_cli_capabilities as get_cli_capabilities
from ornata.rendering.core.capabilities import get_gui_capabilities as get_gui_capabilities
from ornata.rendering.core.capabilities import get_tty_capabilities as get_tty_capabilities
from ornata.rendering.core.compositor import Layer as Layer
from ornata.rendering.core.frame import Frame as Frame
from ornata.rendering.core.frame import FrameBuffer as FrameBuffer
from ornata.rendering.core.pipeline import PipelineMetrics as PipelineMetrics
from ornata.rendering.core.pipeline import PipelineStage as PipelineStage
from ornata.rendering.core.pipeline import RenderPipeline as RenderPipeline
from ornata.rendering.core.render_signals import RenderSignal as RenderSignal
from ornata.rendering.core.render_signals import SignalDispatcher as SignalDispatcher
from ornata.rendering.core.render_signals import SignalEmitter as SignalEmitter
from ornata.rendering.core.render_signals import SignalType as SignalType
from ornata.rendering.core.render_signals import get_global_dispatcher as get_global_dispatcher
from ornata.rendering.core.render_signals import get_global_emitter as get_global_emitter

__all__ = [
    "ANSIRenderer",
    "CLIInputPipeline",
    "read_key",
    "Color8",
    "Compositor",
    "ConHostAdapter",
    "EraseMode",
    "Frame",
    "FrameBuffer",
    "GuiApplication",
    "GuiRuntime",
    "GuiStream",
    "InputReader",
    "KeyEvent",
    "Layer",
    "LiveSessionRenderer",
    "MouseEvent",
    "PipelineMetrics",
    "PipelineStage",
    "RenderPipeline",
    "RenderSignal",
    "RenderableBase",
    "Renderer",
    "RendererCapabilities",
    "SignalDispatcher",
    "SignalEmitter",
    "SignalType",
    "Surface",
    "TTYRenderer",
    "TerminalApp",
    "TerminalController",
    "TerminalRenderer",
    "TerminalSession",
    "TerminalState",
    "VT100",
    "Win32EventHandler",
    "Win32Window",
    "WindowRenderer",
    "GuiNodeLike",
    "_draw_box",
    "_draw_panel",
    "_draw_text",
    "_render_node",
    "_safe_fill_rect",
    "ansi",
    "ansi_16_background",
    "ansi_16_by_name",
    "ansi_16_foreground",
    "ansi_256_background",
    "ansi_256_foreground",
    "app",
    "base_renderer",
    "bell",
    "blink",
    "bold",
    "bsd",
    "clear_line",
    "clear_line_from_cursor",
    "clear_line_to_cursor",
    "clear_screen",
    "clear_screen_from_cursor",
    "clear_screen_to_cursor",
    "color_background",
    "color_foreground",
    "combine_styles",
    "compositor",
    "conhost",
    "contexts",
    "create_application",
    "create_cli_input_pipeline",
    "cursor",
    "cursor_column",
    "cursor_get_position",
    "cursor_hide",
    "cursor_move_down",
    "cursor_move_left",
    "cursor_move_right",
    "cursor_move_up",
    "cursor_next_line",
    "cursor_position",
    "cursor_position_from",
    "cursor_prev_line",
    "cursor_restore_position",
    "cursor_save_position",
    "cursor_scroll_down",
    "cursor_scroll_up",
    "cursor_set_style",
    "cursor_show",
    "delete_chars",
    "delete_lines",
    "detect_conhost_capabilities",
    "detect_terminal_capabilities",
    "detector",
    "dim",
    "disable_alternate_screen_buffer",
    "enable_alternate_screen_buffer",
    "enter_alternate_buffer",
    "erase_in_display",
    "erase_in_line",
    "exit_alternate_buffer",
    "font_select",
    "fraktur",
    "frame",
    "get_capabilities",
    "get_cli_capabilities",
    "get_conhost_adapter",
    "get_default_application",
    "get_global_dispatcher",
    "get_global_emitter",
    "get_gui_capabilities",
    "get_runtime",
    "get_terminal_adapter",
    "get_terminal_size",
    "get_text_width",
    "get_tty_capabilities",
    "gui",
    "hidden",
    "input",
    "insert_chars",
    "insert_lines",
    "is_available",
    "is_conhost_available",
    "is_terminal",
    "italic",
    "palette",
    "parse_cursor_position_response",
    "parse_mouse_event",
    "platform",
    "rapid_blink",
    "register",
    "render_signals",
    "render_tree",
    "renderer",
    "report_cursor_position",
    "report_device_attributes",
    "report_window_size",
    "reset_all",
    "reset_background",
    "reset_blink",
    "reset_bold_dim",
    "reset_colors",
    "reset_foreground",
    "reset_hidden",
    "reset_italic",
    "reset_reverse",
    "reset_scroll_region",
    "reset_strikethrough",
    "reset_underline",
    "reverse",
    "screen_buffer",
    "scroll_down",
    "scroll_up",
    "session",
    "set_default_colors",
    "set_scroll_region",
    "set_window_title",
    "sgr",
    "sgr_code",
    "sgr_codes",
    "strikethrough",
    "style_from_text_style",
    "subscript",
    "superscript",
    "terminal",
    "terminal_app",
    "termios",
    "true_color_foreground",
    "tty",
    "underline",
    "underline_double",
    "vt100",
    "win32",
    "VDOMAdapter",
]
