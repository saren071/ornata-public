"""Terminal live app loop supporting input and ticking.

This is a minimal adapter that keeps the same public shape while removing
hard dependencies on a separate mouse module.
"""

from __future__ import annotations

import os
import time as _t
from typing import TYPE_CHECKING, TextIO

from ornata.api.exports.definitions import BackendTarget, Event, EventType, KeyEvent, KeyEventType, QuitEvent, TickEvent
from ornata.api.exports.events import EventBus
from ornata.api.exports.interop import kernel32
from ornata.api.exports.utils import get_logger
from ornata.rendering.backends.cli.input import read_key
from ornata.rendering.backends.cli.session import LiveSessionRenderer

if TYPE_CHECKING:
    from collections.abc import Callable


def enable_mouse_reporting() -> str:
    return "\x1b[?1000;1002;1006;1004h"


def disable_mouse_reporting() -> str:
    return "\x1b[?1000;1002;1006;1004l"


def hide_cursor() -> str:
    return "\x1b[?25l"


def show_cursor() -> str:
    return "\x1b[?25h"


def enter_alternate_buffer() -> str:
    return "\x1b[?1049h"


def exit_alternate_buffer() -> str:
    return "\x1b[?1049l"


def _enable_vt_mode(stream: TextIO, logger) -> None:
    """Enable Windows VT processing/input when possible."""

    if os.name != "nt":
        logger.debug("terminal_session: VT mode not required on %s", os.name)
        return

    if kernel32.GetStdHandle is None or kernel32.GetConsoleMode is None or kernel32.SetConsoleMode is None:
        logger.warning("terminal_session: kernel32 console bindings unavailable")
        return

    handles = {
        "out": kernel32.GetStdHandle(kernel32.STD_OUTPUT_HANDLE),
        "in": kernel32.GetStdHandle(kernel32.STD_INPUT_HANDLE),
    }
    for name, handle in handles.items():
        if handle in (0, None, kernel32.INVALID_HANDLE_VALUE):
            logger.debug("terminal_session: no handle for %s stream", name)
            continue
        mode_value = kernel32.get_console_mode(handle)
        if mode_value is None:
            logger.debug("terminal_session: GetConsoleMode failed for %s", name)
            continue
        target_bits = 0x0004 if name == "out" else 0x0200
        if mode_value & target_bits:
            logger.debug("terminal_session: VT flags already set for %s (mode=%#x)", name, mode_value)
            continue
        new_mode = mode_value | target_bits
        if kernel32.set_console_mode(handle, new_mode):
            logger.debug(
                "terminal_session: enabled VT for %s (mode=%#x -> %#x)", name, mode_value, new_mode
            )
        else:
            logger.debug("terminal_session: failed to set VT mode for %s (mode=%#x)", name, mode_value)


class TerminalSession(LiveSessionRenderer):
    """Extended live session with input-driven app loop support."""

    def __init__(self, stream: TextIO) -> None:
        super().__init__(BackendTarget.CLI)
        self._bus = EventBus()
        self._running = False
        self._stream = stream
        self._logger = get_logger(__name__)

    @property
    def events(self) -> EventBus:
        """Access the event bus for subscribing to input and timer events."""
        return self._bus

    def run(self, app: TerminalApp, *, fps: float = 30.0) -> None:
        """Run the application in a live terminal session with input handling."""
        self._logger.debug("terminal_session: running app %r", app)
        self._running = True
        app.attach(self._bus)
        frame: str = app.render()
        _enable_vt_mode(self._stream, self._logger)
        # Enable mouse reporting in terminal
        try:
            self._stream.write(
                enter_alternate_buffer() + hide_cursor() + enable_mouse_reporting() + frame
            )
            self._logger.debug(
                "terminal_session: sent enable_mouse_reporting (frame=%d chars)",
                len(frame),
            )
        except Exception:
            self._stream.write(frame)

        interval = 1.0 / max(1e-6, fps)
        last = _t.perf_counter()
        idle_cycles = 0
        while self._running and not app.should_quit:
            now = _t.perf_counter()
            dt = now - last
            last = now
            self._bus.publish(Event(type=EventType.TICK, data=TickEvent(dt=dt)))
            key = read_key(timeout=0.0)
            if key:
                idle_cycles = 0
                self._logger.debug("terminal_session: read key %r", key)
                self._bus.publish(
                    Event(
                        type=EventType.KEY_DOWN,
                        data=KeyEvent(event_type=KeyEventType.KEYDOWN, key=key),
                    )
                )
            else:
                idle_cycles += 1
                if idle_cycles >= int(fps):  # log once per second of idle time
                    self._logger.debug("terminal_session: no input detected for %.1fs", idle_cycles / fps)
                    idle_cycles = 0
            new_frame = app.render()
            if new_frame != frame:
                frame = new_frame
                self._logger.debug("terminal_session: new frame rendered (len=%d)", len(new_frame))
                self._stream.write(frame)
            sleep_for = interval - (_t.perf_counter() - now)
            if sleep_for > 0:
                _t.sleep(sleep_for)
        self._logger.debug("terminal_session: publishing window close (running=%s, should_quit=%s)", self._running, app.should_quit)
        self._bus.publish(Event(type=EventType.WINDOW_CLOSE, data=QuitEvent()))
        app.detach()
        # Disable mouse reporting
        try:
            self._stream.write(disable_mouse_reporting() + show_cursor() + exit_alternate_buffer())
            self._logger.debug("terminal_session: sent disable_mouse_reporting")
        except Exception:
            pass

    def stop(self) -> None:
        """Stop the running session loop."""
        self._logger.debug("terminal_session: stop() called")
        self._running = False


class TerminalApp:
    """Base class for custom terminal applications."""

    def __init__(self) -> None:
        self._bus: EventBus | None = None
        self.should_quit: bool = False
        self._subs: list[Callable[[], None]] = []

    def attach(self, bus: EventBus) -> None:
        """Attach the app to an event bus."""
        self._bus = bus
        self._subs.append(bus.subscribe(EventType.KEY_DOWN.value, self._on_key_event))
        self._subs.append(bus.subscribe(EventType.TICK.value, self._on_tick_event))
        self._subs.append(bus.subscribe(EventType.WINDOW_CLOSE.value, self._on_quit_event))

    def detach(self) -> None:
        """Detach the app and unsubscribe from events."""
        for unsub in self._subs:
            try:
                unsub()
            except Exception:
                pass
        self._subs.clear()
        self._bus = None

    def _on_key_event(self, evt: Event) -> None:
        try:
            payload = evt.data
            if isinstance(payload, KeyEvent):
                self.on_key(payload.key)
        except Exception:  #
            pass

    def _on_tick_event(self, evt: Event) -> None:
        try:
            payload = evt.data
            if isinstance(payload, TickEvent):
                self.on_tick(payload.dt)
        except Exception:
            pass

    def _on_quit_event(self, evt: Event) -> None:
        try:
            if isinstance(evt.data, QuitEvent) or evt.type is EventType.WINDOW_CLOSE:
                self.should_quit = True
        except Exception:
            pass

    def on_key(self, key: str) -> None:
        if key in ("q", "escape", "ctrl+c"):
            self.should_quit = True

    def on_tick(self, dt: float) -> None:
        _ = dt

    def render(self) -> str:
        return ""
