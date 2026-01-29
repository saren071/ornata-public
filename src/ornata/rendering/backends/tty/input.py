"""TTY input handling and event parsing.

Handles keyboard input, mouse events, and special key sequences in raw
terminal mode with support for Windows platforms.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ornata.api.exports.definitions import KeyEvent, MouseEvent

logger = get_logger(__name__)


class InputReader:
    """Cross-platform TTY input reader.
    
    Reads raw input from stdin with support for escape sequences,
    function keys, and mouse events.
    
    Returns
    -------
    InputReader
        Input reader instance.
    """

    def __init__(self) -> None:
        """Initialize the input reader.
        
        Returns
        -------
        None
        """
        self._buffer: list[str] = []
        logger.debug("Initialized InputReader")

    def read_key(self, timeout: float = 0.0) -> KeyEvent | None:
        """Read a single key event.
        
        Parameters
        ----------
        timeout : float
            Timeout in seconds (0 = non-blocking).
        
        Returns
        -------
        KeyEvent | None
            Key event or None if no input.
        """
        from ornata.api.exports.definitions import KeyEvent, KeyEventType
        char = self._read_char(timeout)
        if char is None:
            return None

        if char == "\x1b":  # ESC
            return self._parse_escape_sequence()

        return KeyEvent(
            event_type=KeyEventType.KEYDOWN,
            key=char,
            char=char if char.isprintable() else None,
            ctrl=ord(char) < 32,
        )

    def read_events(self, timeout: float = 0.0) -> Iterator[KeyEvent | MouseEvent]:
        """Read all available events.
        
        Parameters
        ----------
        timeout : float
            Initial timeout in seconds.
        
        Yields
        ------
        KeyEvent | MouseEvent
            Input events as they arrive.
        """
        event = self.read_key(timeout)
        while event is not None:
            yield event
            event = self.read_key(0.0)

    def _read_char(self, timeout: float = 0.0) -> str | None:
        """Read a single character from stdin.
        
        Parameters
        ----------
        timeout : float
            Timeout in seconds.
        
        Returns
        -------
        str | None
            Character or None if no input.
        """
        if self._buffer:
            return self._buffer.pop(0)

        return self._read_char_windows(timeout)

    def _read_char_windows(self, timeout: float) -> str | None:
        """Read character on Windows systems.
        
        Parameters
        ----------
        timeout : float
            Timeout in seconds.
        
        Returns
        -------
        str | None
            Character or None.
        """
        try:
            import msvcrt

            if msvcrt.kbhit():
                return msvcrt.getch().decode("utf-8", errors="replace")
            return None
        except Exception as e:
            logger.warning(f"Failed to read Windows input: {e}")
            return None

    def _parse_escape_sequence(self) -> KeyEvent:
        """Parse an escape sequence into a key event.
        
        Returns
        -------
        KeyEvent
            Parsed key event.
        """
        from ornata.api.exports.definitions import KeyEvent, KeyEventType
        seq = self._read_escape_sequence()

        key_map = {
            "[A": "up",
            "[B": "down",
            "[C": "right",
            "[D": "left",
            "[H": "home",
            "[F": "end",
            "[2~": "insert",
            "[3~": "delete",
            "[5~": "page_up",
            "[6~": "page_down",
            "OP": "f1",
            "OQ": "f2",
            "OR": "f3",
            "OS": "f4",
            "[15~": "f5",
            "[17~": "f6",
            "[18~": "f7",
            "[19~": "f8",
            "[20~": "f9",
            "[21~": "f10",
            "[23~": "f11",
            "[24~": "f12",
        }

        key = key_map.get(seq, "escape")
        return KeyEvent(event_type=KeyEventType.KEYDOWN, key=key)

    def _read_escape_sequence(self) -> str:
        """Read the remainder of an escape sequence.
        
        Returns
        -------
        str
            The escape sequence (without the initial ESC).
        """
        seq = ""
        for _ in range(10):  # Max sequence length
            char = self._read_char(0.01)  # Short timeout
            if char is None:
                break
            seq += char
            if char in ("~", "A", "B", "C", "D", "H", "F", "P", "Q", "R", "S"):
                break
        return seq


def parse_mouse_event(seq: str) -> MouseEvent | None:
    """Parse a mouse event escape sequence.
    
    Parameters
    ----------
    seq : str
        Escape sequence to parse.
    
    Returns
    -------
    MouseEvent | None
        Parsed mouse event or None if invalid.
    """
    from ornata.api.exports.definitions import MouseEvent, MouseEventType
    if not seq.startswith("[<") or not seq.endswith(("M", "m")):
        return None

    try:
        parts = seq[2:-1].split(";")
        if len(parts) != 3:
            return None

        button = int(parts[0])
        x = int(parts[1])
        y = int(parts[2])
        is_release = seq.endswith("m")

        event_type = MouseEventType.BUTTON_UP if is_release else MouseEventType.BUTTON_DOWN

        return MouseEvent(event_type=event_type, x=x, y=y, button=button)
    except (ValueError, IndexError) as e:
        logger.warning(f"Failed to parse mouse event: {e}")
        return None
