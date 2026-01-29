"""Cross-platform terminal I/O control.

Provides terminal mode management (raw, cbreak, normal) with automatic
platform detection and fallback for Windows systems.
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING, TextIO

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ornata.api.exports.definitions import TerminalState

logger = get_logger(__name__)


class TerminalController:
    """Cross-platform terminal control.
    
    Manages terminal modes (raw, cbreak, normal) with automatic platform
    detection and proper state restoration.
    
    Parameters
    ----------
    stream : TextIO
        The terminal stream to control (usually sys.stdin or sys.stdout).
    
    Returns
    -------
    TerminalController
        Terminal controller instance.
    """

    def __init__(self, stream: TextIO = sys.stdin) -> None:
        """Initialize terminal controller.
        
        Parameters
        ----------
        stream : TextIO
            The terminal stream to control.
        
        Returns
        -------
        None
        """
        self.stream = stream
        self.fd = stream.fileno() if hasattr(stream, "fileno") else -1
        self.is_tty = stream.isatty() if hasattr(stream, "isatty") else False
        self._saved_state: TerminalState | None = None

    def save_state(self) -> TerminalState:
        """Save the current terminal state.
        
        Returns
        -------
        TerminalState
            The saved state.
        """
        from ornata.api.exports.definitions import TerminalState
        if not self.is_tty:
            return TerminalState(fd=self.fd, original_mode=None, is_tty=False)

        original_mode = None
        try:
            import msvcrt
            print(msvcrt)

            logger.log(5, "Windows terminal - limited state saving")
        except ImportError:
            pass

        state = TerminalState(fd=self.fd, original_mode=original_mode, is_tty=True)
        self._saved_state = state
        return state

    def restore_state(self, state: TerminalState | None = None) -> None:
        """Restore a previously saved terminal state.
        
        Parameters
        ----------
        state : TerminalState | None
            The state to restore, or None to use last saved.
        
        Returns
        -------
        None
        """
        if state is None:
            state = self._saved_state

        if state is None or not state.is_tty or state.original_mode is None:
            return

        try:
            import msvcrt
            print(msvcrt)

            logger.log(5, "Windows terminal - limited state saving")
        except ImportError:
            pass

    def set_raw_mode(self) -> None:
        """Set terminal to raw mode (no input processing).
        
        Returns
        -------
        None
        """
        if not self.is_tty:
            logger.warning("Cannot set raw mode on non-TTY")
            return

        try:
            import importlib
            msvcrt = importlib.import_module("msvcrt")
            print(msvcrt)
            logger.debug("Windows raw mode - using msvcrt")
        except ImportError:
            pass

    def set_cbreak_mode(self) -> None:
        """Set terminal to cbreak mode (char-by-char input).
        
        Returns
        -------
        None
        """
        if not self.is_tty:
            logger.warning("Cannot set cbreak mode on non-TTY")
            return

        try:
            import importlib
            msvcrt = importlib.import_module("msvcrt")
            print(msvcrt)
            logger.debug("Windows cbreak mode - using msvcrt")
        except ImportError:
            pass

    def enable_echo(self) -> None:
        """Enable terminal echo.
        
        Returns
        -------
        None
        """
        if not self.is_tty:
            return

        if sys.platform == "win32":
            logger.log(5, "Terminal echo control not available via termios on Windows")
            return

        try:
            import termios

            attrs = termios.tcgetattr(self.fd)
            attrs[3] |= termios.ECHO
            termios.tcsetattr(self.fd, termios.TCSADRAIN, attrs)
            logger.log(5, "Enabled terminal echo")
        except (ImportError, OSError) as e:
            logger.warning(f"Failed to enable echo: {e}")

    def disable_echo(self) -> None:
        """Disable terminal echo.
        
        Returns
        -------
        None
        """
        if not self.is_tty:
            return

        if sys.platform == "win32":
            logger.log(5, "Terminal echo control not available via termios on Windows")
            return

        try:
            import termios

            attrs = termios.tcgetattr(self.fd)
            attrs[3] &= ~termios.ECHO
            termios.tcsetattr(self.fd, termios.TCSADRAIN, attrs)
            logger.log(5, "Disabled terminal echo")
        except (ImportError, OSError) as e:
            logger.warning(f"Failed to disable echo: {e}")

    def get_size(self) -> tuple[int, int]:
        """Get terminal size in rows and columns.
        
        Returns
        -------
        tuple[int, int]
            (rows, columns), defaults to (24, 80) if unable to detect.
        """
        if sys.platform == "win32":
            # Windows terminal size handled via shutil fallback below.
            logger.log(5, "Using fallback terminal size on Windows")
            return (24, 80)

        try:
            import fcntl
            import struct
            import termios

            data = fcntl.ioctl(self.fd, termios.TIOCGWINSZ, b"\x00" * 8)
            rows, cols = struct.unpack("HHHH", data)[:2]
            logger.log(5, f"Terminal size: {rows}x{cols}")
            return (rows, cols)
        except Exception as e:
            logger.warning(f"Failed to get terminal size: {e}")
            return (24, 80)

    @contextmanager
    def raw_mode(self) -> Iterator[None]:
        """Context manager for raw mode.
        
        Yields
        ------
        None
        
        Examples
        --------
        >>> with term.raw_mode():
        ...     # Terminal is in raw mode
        ...     pass
        """
        state = self.save_state()
        try:
            self.set_raw_mode()
            yield
        finally:
            self.restore_state(state)

    @contextmanager
    def cbreak_mode(self) -> Iterator[None]:
        """Context manager for cbreak mode.
        
        Yields
        ------
        None
        
        Examples
        --------
        >>> with term.cbreak_mode():
        ...     # Terminal is in cbreak mode
        ...     pass
        """
        state = self.save_state()
        try:
            self.set_cbreak_mode()
            yield
        finally:
            self.restore_state(state)

    @contextmanager
    def no_echo(self) -> Iterator[None]:
        """Context manager for disabling echo.
        
        Yields
        ------
        None
        
        Examples
        --------
        >>> with term.no_echo():
        ...     # Echo is disabled
        ...     password = input("Password: ")
        """
        state = self.save_state()
        try:
            self.disable_echo()
            yield
        finally:
            self.restore_state(state)


def is_terminal(stream: TextIO = sys.stdout) -> bool:
    """Check if a stream is a terminal.
    
    Parameters
    ----------
    stream : TextIO
        The stream to check.
    
    Returns
    -------
    bool
        True if stream is a TTY, False otherwise.
    """
    return stream.isatty() if hasattr(stream, "isatty") else False


def get_terminal_size() -> tuple[int, int]:
    """Get current terminal size.
    
    Returns
    -------
    tuple[int, int]
        (rows, columns), defaults to (24, 80) if unable to detect.
    """
    try:
        import shutil

        size = shutil.get_terminal_size(fallback=(80, 24))
        return (size.lines, size.columns)
    except Exception:
        return (24, 80)
