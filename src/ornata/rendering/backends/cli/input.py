"""CLI input pipeline that drives the event subsystem with keyboard input.

This module provides a cooperative input loop that converts raw keyboard
input into :class:`~ornata.events.core.types.Event` instances and dispatches
them through the event subsystem without relying on legacy helpers.
"""

from __future__ import annotations

import sys
import threading
import time
from typing import TYPE_CHECKING

from ornata.api.exports.definitions import Event, EventPriority, EventType, KeyEvent, KeyEventType
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.events import EventSubsystem

logger = get_logger(__name__)


class CLIInputPipeline:
    """Manages keyboard input and converts it to events for the subsystem."""

    def __init__(self, event_subsystem: EventSubsystem) -> None:
        """Initialize the CLI input pipeline.

        Args:
            event_subsystem: Event subsystem to dispatch input events to.
        """
        self._event_subsystem = event_subsystem
        self._running = False
        self._input_thread: threading.Thread | None = None
        self._shutdown_event = threading.Event()
        self._input_available = threading.Event()
        self._last_key_time = 0.0
        self._key_repeat_delay = 0.5  # seconds before key repeat starts
        self._key_repeat_rate = 0.05  # seconds between repeats
        self._last_key_token_value: str | None = None
        self._last_tick_time_value = 0.0

    def start(self) -> None:
        """Start the input pipeline."""
        if self._running:
            logger.warning("CLI input pipeline already running")
            return

        self._running = True
        self._shutdown_event.clear()
        self._input_thread = threading.Thread(
            target=self._input_loop,
            name="cli-input-pipeline",
            daemon=True
        )
        self._input_thread.start()
        logger.debug("CLI input pipeline started")

    def stop(self) -> None:
        """Stop the input pipeline."""
        if not self._running:
            return

        self._running = False
        self._shutdown_event.set()

        if self._input_thread and self._input_thread.is_alive():
            self._input_thread.join(timeout=1.0)
            if self._input_thread.is_alive():
                logger.warning("CLI input thread did not stop gracefully")

        self._input_thread = None
        logger.debug("CLI input pipeline stopped")

    def _input_loop(self) -> None:
        """Main input processing loop."""
        logger.debug("CLI input loop started")

        try:
            while self._running and not self._shutdown_event.is_set():
                try:
                    # Check for input availability with timeout
                    if self._wait_for_input(timeout=0.1):
                        key_token = self._read_key()
                        if key_token:
                            self._dispatch_key_event(key_token)
                    else:
                        # No input available, check if we should send a tick event
                        self._maybe_send_tick_event()

                except KeyboardInterrupt:
                    # Handle Ctrl+C gracefully
                    quit_event = Event(
                        type=EventType.KEY_DOWN,
                        data=KeyEvent(
                            event_type=KeyEventType.KEYDOWN,
                            key="c",
                            char="c",
                            modifiers=frozenset({"ctrl"}),
                            ctrl=True,
                            alt=False,
                            shift=False,
                            repeat=False,
                        ),
                        priority=EventPriority.CRITICAL,
                        source="cli_input",
                    )
                    self._event_subsystem.dispatch_event(quit_event)
                    break
                except Exception as e:
                    logger.error("Error in CLI input loop: %s", e)
                    time.sleep(0.1)  # Brief pause before retry

        except Exception as e:
            logger.error("Fatal error in CLI input loop: %s", e)
        finally:
            logger.debug("CLI input loop ended")

    @staticmethod
    def wait_for_input(timeout: float = 0.1) -> bool:
        """Public wrapper around the low-level input wait helper.

        Parameters
        ----------
        timeout : float
            Maximum time to wait in seconds.

        Returns
        -------
        bool
            True if input is available, False otherwise.
        """
        return CLIInputPipeline._wait_for_input(timeout)

    @staticmethod
    def _wait_for_input(timeout: float = 0.1) -> bool:
        """Wait for input to become available.

        Args:
            timeout: Maximum time to wait in seconds.

        Returns:
            True if input is available, False if timeout occurred.
        """
        if sys.platform.startswith("win"):
            try:
                import msvcrt
                return msvcrt.kbhit()
            except ImportError:
                pass

        # POSIX path
        try:
            import select
            ready, _, _ = select.select([sys.stdin], [], [], timeout)
            if ready:
                logger.debug("cli_input: select detected pending input")
            return bool(ready)
        except (ImportError, OSError):
            # Fallback - just sleep
            time.sleep(timeout)
            return False

    @staticmethod
    def _read_key() -> str | None:
        """Read a single key press and return semantic token.

        Returns:
            Key token string or None if no key was read.
        """
        if sys.platform.startswith("win"):
            try:
                import msvcrt

                if not msvcrt.kbhit():
                    return None

                ch = msvcrt.getwch()
                logger.debug("cli_input: raw key %r", ch)

                # Handle special keys
                if ch in ("\r", "\n"):
                    logger.debug("cli_input: normalized enter key")
                    return "enter"
                if ch == "\x1b":
                    logger.debug("cli_input: escape key")
                    return "escape"
                if ch == "\x00" or ch == "\xe0":
                    code = msvcrt.getwch()
                    logger.debug("cli_input: extended key prefix %r", code)
                    mapping = {
                        "H": "up",
                        "P": "down",
                        "K": "left",
                        "M": "right",
                        "I": "page_up",
                        "Q": "page_down",
                        "G": "home",
                        "O": "end",
                    }
                    return mapping.get(code, "")
                if ch == "\x08":
                    logger.debug("cli_input: backspace key")
                    return "backspace"
                if ch == "\t":
                    logger.debug("cli_input: tab key")
                    return "tab"
                return ch
            except ImportError:
                logger.warning("CLI input: msvcrt unavailable on Windows platform")
                return None
        else:
            try:
                import importlib
                import select
                from typing import Any

                termios: Any = importlib.import_module("termios")
                tty: Any = importlib.import_module("tty")

                if not select.select([sys.stdin], [], [], 0)[0]:
                    return None

                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)

                try:
                    tty.setraw(fd)
                    first = sys.stdin.read(1)

                    if first == "\x1b":  # ESC sequence
                        seq = ""
                        while select.select([sys.stdin], [], [], 0.01)[0]:
                            ch = sys.stdin.read(1)
                            seq += ch
                            if ch.isalpha() or ch == "~":
                                break

                        keymap = {
                            "[A": "up",
                            "[B": "down",
                            "[C": "right",
                            "[D": "left",
                            "[H": "home",
                            "[F": "end",
                            "[1~": "home",
                            "[4~": "end",
                            "[2~": "insert",
                            "[3~": "delete",
                            "[5~": "page_up",
                            "[6~": "page_down",
                            "OP": "f1",
                            "OQ": "f2",
                            "OR": "f3",
                            "OS": "f4",
                        }

                        seq_norm = seq.replace(" ", "")
                        if seq_norm.startswith("[") or seq_norm.startswith("O"):
                            token = seq_norm
                        else:
                            token = seq_norm
                        return keymap.get(token, "escape")

                    if first in ("\r", "\n"):
                        return "enter"
                    if first == "\t":
                        return "tab"
                    if first == " ":
                        return "space"
                    if first == "\x7f":
                        return "backspace"
                    return first.lower()

                finally:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

            except (ImportError, OSError):
                pass

        # Fallback input
        try:
            data = input()
            data = data.strip()
            if not data:
                return "enter"
            return data.lower()
        except (EOFError, OSError):
            return None

    @staticmethod
    def read_key() -> str | None:
        """Public wrapper that reads a single key token when available.

        Returns
        -------
        str | None
            Semantic key token or None if no key is ready.
        """
        return CLIInputPipeline._read_key()

    def _dispatch_key_event(self, key_token: str) -> None:
        """Convert key token to Event and dispatch through subsystem.

        Args:
            key_token: Semantic key token from input reading.
        """
        current_time = time.perf_counter()
        is_repeat = False

        # Handle key repeat logic
        if key_token == self._last_key_token and (current_time - self._last_key_time) > self._key_repeat_delay:
            if (current_time - self._last_key_time) > (self._key_repeat_rate * 2):  # Reset repeat after pause
                self._last_key_time = current_time
            else:
                is_repeat = True
        else:
            self._last_key_token = key_token
            self._last_key_time = current_time

        # Create key event data
        modifiers: set[str] = set()
        base_key = key_token

        # Extract modifiers from key token
        if "ctrl+" in key_token:
            modifiers.add("ctrl")
            base_key = key_token.replace("ctrl+", "")
        if "alt+" in key_token:
            modifiers.add("alt")
            base_key = key_token.replace("alt+", "")
        if "shift+" in key_token:
            modifiers.add("shift")
            base_key = key_token.replace("shift+", "")

        key_event_data = KeyEvent(
            event_type=KeyEventType.KEYDOWN,
            key=base_key,
            char=base_key if len(base_key) == 1 else None,
            modifiers=frozenset(modifiers),
            ctrl="ctrl" in modifiers,
            alt="alt" in modifiers,
            shift="shift" in modifiers,
            repeat=is_repeat,
        )

        # Create and dispatch event
        event = Event(
            type=EventType.KEY_DOWN,
            data=key_event_data,
            priority=EventPriority.NORMAL,
            timestamp=current_time,
            source="cli_input",
        )

        self._event_subsystem.dispatch_event(event)
        logger.log(5, "Dispatched key event: %s", key_token)

    def _maybe_send_tick_event(self) -> None:
        """Send periodic tick events when no input is available."""
        current_time = time.perf_counter()
        # Send tick events at ~60 FPS when idle
        if current_time - self._last_tick_time > (1.0 / 60.0):
            tick_event = Event(
                type=EventType.TICK,
                priority=EventPriority.LOW,
                source="cli_input",
                timestamp=current_time
            )
            self._event_subsystem.dispatch_event(tick_event)
            self._last_tick_time = current_time

    @property
    def _last_key_token(self) -> str | None:
        """Return the last key token processed for repeat detection."""
        return self._last_key_token_value

    @_last_key_token.setter
    def _last_key_token(self, value: str | None) -> None:
        """Store the latest key token for repeat detection logic."""
        self._last_key_token_value = value

    @property
    def _last_tick_time(self) -> float:
        """Return the timestamp of the last dispatched tick event."""
        return self._last_tick_time_value

    @_last_tick_time.setter
    def _last_tick_time(self, value: float) -> None:
        """Record when the most recent tick event was dispatched."""
        self._last_tick_time_value = value


def read_key(timeout: float = 0.0) -> str | None:
    """Return a semantic key token if available within ``timeout`` seconds."""
    if CLIInputPipeline.wait_for_input(timeout):
        return CLIInputPipeline.read_key()
    return None


def create_cli_input_pipeline(event_subsystem: EventSubsystem) -> CLIInputPipeline:
    """Create a new CLI input pipeline instance.

    Args:
        event_subsystem: Event subsystem to dispatch events to.

    Returns:
        CLIInputPipeline: New pipeline instance.
    """
    return CLIInputPipeline(event_subsystem)
