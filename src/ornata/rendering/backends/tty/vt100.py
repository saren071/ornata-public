"""VT100/ANSI escape sequence generation.

Provides a comprehensive set of VT100 and ANSI escape sequences for
terminal control, cursor movement, colors, and text attributes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ornata.api.exports.definitions import EraseMode
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Color8


logger = get_logger(__name__)


@dataclass(frozen=True)
class VT100:
    """VT100 escape sequence generator.
    
    Provides methods to generate VT100/ANSI escape sequences for terminal
    control without maintaining state.
    
    Returns
    -------
    VT100
        VT100 sequence generator instance.
    """

    @staticmethod
    def cursor_up(n: int = 1) -> str:
        """Move cursor up n lines.
        
        Parameters
        ----------
        n : int
            Number of lines to move up.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}{n}A"

    @staticmethod
    def cursor_down(n: int = 1) -> str:
        """Move cursor down n lines.
        
        Parameters
        ----------
        n : int
            Number of lines to move down.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}{n}B"

    @staticmethod
    def cursor_forward(n: int = 1) -> str:
        """Move cursor forward n columns.
        
        Parameters
        ----------
        n : int
            Number of columns to move forward.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}{n}C"

    @staticmethod
    def cursor_back(n: int = 1) -> str:
        """Move cursor back n columns.
        
        Parameters
        ----------
        n : int
            Number of columns to move back.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}{n}D"

    @staticmethod
    def cursor_position(row: int = 1, col: int = 1) -> str:
        """Move cursor to specific position.
        
        Parameters
        ----------
        row : int
            Row number (1-indexed).
        col : int
            Column number (1-indexed).
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}{row};{col}H"

    @staticmethod
    def cursor_save() -> str:
        """Save cursor position.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import ESC
        return f"{ESC}7"

    @staticmethod
    def cursor_restore() -> str:
        """Restore cursor position.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import ESC
        return f"{ESC}8"

    @staticmethod
    def cursor_show() -> str:
        """Show cursor.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}?25h"

    @staticmethod
    def cursor_hide() -> str:
        """Hide cursor.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}?25l"

    @staticmethod
    def erase_display(mode: EraseMode = EraseMode.ALL) -> str:
        """Erase display.
        
        Parameters
        ----------
        mode : EraseMode
            Erase mode (TO_END, TO_START, or ALL).
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}{mode.value}J"

    @staticmethod
    def erase_line(mode: EraseMode = EraseMode.ALL) -> str:
        """Erase line.
        
        Parameters
        ----------
        mode : EraseMode
            Erase mode (TO_END, TO_START, or ALL).
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}{mode.value}K"

    @staticmethod
    def scroll_up(n: int = 1) -> str:
        """Scroll up n lines.
        
        Parameters
        ----------
        n : int
            Number of lines to scroll.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}{n}S"

    @staticmethod
    def scroll_down(n: int = 1) -> str:
        """Scroll down n lines.
        
        Parameters
        ----------
        n : int
            Number of lines to scroll.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}{n}T"

    @staticmethod
    def sgr(*codes: int) -> str:
        """Set graphics rendition.
        
        Parameters
        ----------
        *codes : int
            SGR codes to apply.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI, SGRCode
        if not codes:
            codes = (SGRCode.RESET,)
        return f"{CSI}{';'.join(str(c) for c in codes)}m"

    @staticmethod
    def reset() -> str:
        """Reset all attributes.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import SGRCode
        return VT100.sgr(SGRCode.RESET)

    @staticmethod
    def fg_color_8(color: Color8) -> str:
        """Set foreground to 8-color.
        
        Parameters
        ----------
        color : Color8
            The color to set.
        
        Returns
        -------
        str
            The escape sequence.
        """
        return VT100.sgr(30 + color.value)

    @staticmethod
    def bg_color_8(color: Color8) -> str:
        """Set background to 8-color.
        
        Parameters
        ----------
        color : Color8
            The color to set.
        
        Returns
        -------
        str
            The escape sequence.
        """
        return VT100.sgr(40 + color.value)

    @staticmethod
    def fg_color_256(color: int) -> str:
        """Set foreground to 256-color.
        
        Parameters
        ----------
        color : int
            Color index (0-255).
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}38;5;{color}m"

    @staticmethod
    def bg_color_256(color: int) -> str:
        """Set background to 256-color.
        
        Parameters
        ----------
        color : int
            Color index (0-255).
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}48;5;{color}m"

    @staticmethod
    def fg_color_rgb(r: int, g: int, b: int) -> str:
        """Set foreground to RGB color.
        
        Parameters
        ----------
        r : int
            Red (0-255).
        g : int
            Green (0-255).
        b : int
            Blue (0-255).
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}38;2;{r};{g};{b}m"

    @staticmethod
    def bg_color_rgb(r: int, g: int, b: int) -> str:
        """Set background to RGB color.
        
        Parameters
        ----------
        r : int
            Red (0-255).
        g : int
            Green (0-255).
        b : int
            Blue (0-255).
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}48;2;{r};{g};{b}m"

    @staticmethod
    def set_title(title: str) -> str:
        """Set terminal window title.
        
        Parameters
        ----------
        title : str
            Window title.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import BEL, OSC
        return f"{OSC}2;{title}{BEL}"

    @staticmethod
    def alternate_screen_enable() -> str:
        """Enable alternate screen buffer.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}?1049h"

    @staticmethod
    def alternate_screen_disable() -> str:
        """Disable alternate screen buffer.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}?1049l"

    @staticmethod
    def mouse_tracking_enable() -> str:
        """Enable mouse tracking.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}?1000h{CSI}?1002h{CSI}?1015h{CSI}?1006h"

    @staticmethod
    def mouse_tracking_disable() -> str:
        """Disable mouse tracking.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}?1000l{CSI}?1002l{CSI}?1015l{CSI}?1006l"

    @staticmethod
    def bracketed_paste_enable() -> str:
        """Enable bracketed paste mode.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}?2004h"

    @staticmethod
    def bracketed_paste_disable() -> str:
        """Disable bracketed paste mode.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}?2004l"

    @staticmethod
    def request_cursor_position() -> str:
        """Request cursor position report.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}6n"

    @staticmethod
    def request_device_attributes() -> str:
        """Request device attributes.
        
        Returns
        -------
        str
            The escape sequence.
        """
        from ornata.api.exports.definitions import CSI
        return f"{CSI}c"


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text.
    
    Parameters
    ----------
    text : str
        Text with ANSI sequences.
    
    Returns
    -------
    str
        Text without ANSI sequences.
    """
    import re

    ansi_escape = re.compile(r"\x1b\[[0-9;]*[mGKHJABCDsuflh]|\x1b[78]|\x1b\][^\x07]*\x07")
    return ansi_escape.sub("", text)


def get_text_width(text: str) -> int:
    """Get display width of text (excluding ANSI sequences).
    
    Parameters
    ----------
    text : str
        Text to measure.
    
    Returns
    -------
    int
        Display width in characters.
    """
    return len(strip_ansi(text))
