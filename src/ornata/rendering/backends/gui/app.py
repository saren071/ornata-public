"""GUI Application class for managing windows and rendering loops.

Provides the main application class that coordinates window creation,
GPU context management, and integration with the event subsystem.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import TYPE_CHECKING, Any

# Use platform abstraction for window creation
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable
    from inspect import Traceback

    from ornata.api.exports.definitions import Event, FrameTiming, GuiNode
    from ornata.api.exports.events import EventSubsystem, SubsystemEventBus
    from ornata.rendering.core.frame import Frame

logger = get_logger(__name__)


class GuiApplication:
    """Main GUI application class."""

    def __init__(self, backend: str = "auto") -> None:
        from ornata.rendering.backends.gui.runtime import get_runtime
        self.backend = self._resolve_backend(backend)
        self._windows: dict[int, Any] = {}
        self._window_lock = threading.RLock()
        self._running = False
        self._render_thread: threading.Thread | None = None
        self._target_fps = 60.0
        self._frame_interval = 1.0 / self._target_fps
        self._frame_history: deque[float] = deque(maxlen=120)
        self._frame_number = 0
        self._frame_lock = threading.RLock()
        self._event_handlers: list[Callable[[], None]] = []

        # Initialize runtime
        self.runtime = get_runtime(create=True)
        self._event_subsystem: EventSubsystem | None = None
        self._event_bus: SubsystemEventBus | None = None
        self._initialize_event_system()

    def _initialize_event_system(self) -> None:
        """Initialise the event subsystem bridge for GUI rendering."""
        from ornata.api.exports.definitions import EventType
        from ornata.api.exports.events import SubsystemEventBus
        from ornata.events.runtime import get_event_subsystem
        try:
            subsystem = get_event_subsystem()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Event subsystem unavailable; GUI events disabled: %s", exc)
            self._event_subsystem = None
            self._event_bus = None
            return

        self._event_subsystem = subsystem
        bus = SubsystemEventBus("rendering.gui")
        subsystem.register_subsystem("rendering.gui", bus)
        self._event_bus = bus

        self._event_handlers.append(bus.subscribe(EventType.KEY_DOWN.value, self._handle_key_event))
        self._event_handlers.append(bus.subscribe(EventType.WINDOW_CLOSE.value, self._handle_window_close))

    def _resolve_backend(self, backend: str) -> str:
        """Resolve the GPU backend to use."""
        from ornata.api.exports.gpu import get_device_manager
        if backend != "auto":
            return backend

        manager = get_device_manager()
        try:
            manager.initialize()
        except Exception as exc:
            logger.warning("GPU device manager initialization failed: %s", exc)

        detected = manager.active_backend_kind()
        if detected in {"directx11", "directx12", "opengl"}:
            return detected

        if detected:
            logger.info("Resolved backend '%s' even though it is not first-class; using it anyway", detected)
            return detected

        logger.info("No GPU backend detected; defaulting to cpu_fallback")
        return "cpu_fallback"

    def create_window(self, title: str, width: int = 800, height: int = 600) -> Any:
        from ornata.rendering.backends.gui.platform.factory import get_platform_interface
        platform_interface = get_platform_interface()
        window_manager = platform_interface.get_window_manager()
        
        if not window_manager.is_window_available():
            from ornata.api.exports.definitions import WindowCreationError
            raise WindowCreationError("Window creation not available on this platform")

        window = window_manager.create_window(title, width, height)

        # Create GPU context for the window
        try:
            window.create_gpu_context(self.backend)
        except Exception as e:
            window.close()
            from ornata.api.exports.definitions import WindowCreationError
            raise WindowCreationError(f"Failed to create GPU context: {e}") from e

        # 🔧 NEW: mark the window as running so _process_events doesn't insta-kill it
        start = getattr(window, "start", None)
        if callable(start):
            start()  # sets window._running = True and records pump thread
        else:
            # Fallback for non-Win32 windows that don’t have start()
            window._running = True

        with self._window_lock:
            window_id = id(window)
            self._windows[window_id] = window

        if self.runtime is not None:
            self.runtime.set_window(window)
        else:
            logger.warning("No runtime available, window will not be connected to runtime")

        logger.info(f"Created window '{title}' with {self.backend} backend")
        return window

    def destroy_window(self, window: Any) -> None:
        """Destroy a window."""
        window_id = id(window)

        with self._window_lock:
            if window_id in self._windows:
                del self._windows[window_id]

        if self.runtime is not None:
            try:
                self.runtime.remove_window(window)
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("Failed to detach window from runtime: %s", exc)

        window.close()
        logger.info(f"Destroyed window '{window.title}'")

    def run(self, fps: float = 60.0) -> None:
        """Run the application main loop."""
        if self._running:
            raise RuntimeError("GUI application loop is already running")
        self._target_fps = max(1.0, float(fps))
        self._frame_interval = 1.0 / self._target_fps
        self._running = True
        self._frame_number = 0
        with self._frame_lock:
            self._frame_history.clear()

        logger.info(f"Starting GUI application with {self.backend} backend at {self._target_fps:.1f} FPS")

        try:
            if self._event_subsystem is not None:
                self._event_subsystem.start_platform_event_loop()

            # Start render loop
            self._render_thread = threading.Thread(target=self._render_loop, daemon=True)
            self._render_thread.start()

            # Main application loop
            while self._running:
                # Check if any windows are still open
                with self._window_lock:
                    if not self._windows:
                        break

                self._process_events()

                time.sleep(min(0.010, self._frame_interval * 0.5))

        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            self._cleanup()

    def run_async(self, fps: float = 60.0) -> threading.Thread:
        """Start the application loop on a dedicated background thread.

        Parameters
        ----------
        fps : float
            Target frames per second for the render loop.

        Returns
        -------
        threading.Thread
            Thread object running :meth:`run`.
        """
        if self._running:
            raise RuntimeError("GUI application loop is already running")
        thread = threading.Thread(target=self.run, args=(fps,), daemon=True)
        thread.start()
        return thread

    def stop(self) -> None:
        """Stop the application."""
        self._running = False

    @property
    def is_running(self) -> bool:
        """Return whether the GUI application loop is currently running."""
        return self._running

    def _render_loop(self) -> None:
        """Main render loop."""
        from ornata.api.exports.definitions import Frame, FrameTiming
        while self._running:
            frame_start = time.perf_counter()
            frame_timing = FrameTiming(
                frame_number=self._frame_number,
                start_time=frame_start,
                target_frame_time=self._frame_interval,
            )
            frame = Frame(frame_number=self._frame_number, timing=frame_timing)
            frame.mark_rendering_start()

            with self._window_lock:
                windows = list(self._windows.values())

            for window in windows:
                try:
                    self._render_window(window, frame)
                except Exception as exc:
                    logger.error(f"Error rendering window '{window.title}': {exc}")

            frame.mark_rendering_complete()
            frame.mark_presented()
            self._update_frame_metrics(frame_timing)
            self._frame_number += 1

            elapsed = time.perf_counter() - frame_start
            sleep_time = max(0.0, self._frame_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _render_window(self, window: Any, frame: Frame) -> None:
        """Render a single window."""
        from ornata.api.exports.definitions import Color
        gpu_context = window.get_gpu_context()
        if not gpu_context:
            frame.metadata.setdefault("fallback_windows", []).append(window.title)
            return

        frame.metadata.setdefault("windows", []).append(window.title)
        gpu_context.make_current()

        node = getattr(window, "_root_node", None)
        if node:
            try:
                window.render_gui_node(node)
            except Exception as exc:
                logger.error("Failed to render stored GUI node for '%s': %s", window.title, exc)
        else:
            # Clear when no GUI node has been attached yet
            gpu_context.clear(Color(0, 0, 0, 255))  # Black background
            gpu_context.present()

    def _update_frame_metrics(self, timing: FrameTiming) -> None:
        """Update rolling frame statistics."""
        duration = timing.total_duration or timing.render_duration
        if duration is None or duration <= 0:
            return
        with self._frame_lock:
            self._frame_history.append(duration)

    @property
    def current_fps(self) -> float:
        """Return the moving-average frames per second."""
        with self._frame_lock:
            if not self._frame_history:
                return 0.0
            average = sum(self._frame_history) / len(self._frame_history)
        if average <= 0:
            return float("inf")
        return 1.0 / average

    def _process_events(self) -> None:
        """Process window events."""
        if self._event_subsystem is not None:
            self._event_subsystem.pump_platform_events()

        # Allow windows to perform any backend-specific polling if implemented
        with self._window_lock:
            windows = list(self._windows.values())
        for window in windows:
            poll_method = getattr(window, "poll", None)
            if callable(poll_method):
                try:
                    poll_method()
                except Exception as exc:  # pragma: no cover - defensive
                    logger.debug("Window poll failed for %s: %s", window.title, exc)

        # Drop windows that have been closed so the app can exit cleanly
        with self._window_lock:
            for window in list(self._windows.values()):
                running = getattr(window, "_running", True)
                handle = getattr(window, "_native_handle", None)
                logger.debug(
                    "Dropping window '%s': running=%s handle=%r",
                    window.title, running, handle
                )
                if not getattr(window, "_running", True) or getattr(window, "_native_handle", None) is None:
                    try:
                        self.destroy_window(window)
                    except Exception as exc:  # pragma: no cover - defensive
                        logger.debug("Failed to destroy closed window %s: %s", window.title, exc)

    def _handle_key_event(self, event: Event) -> None:
        """Handle high-level key events routed through the GUI bus."""
        from ornata.api.exports.definitions import KeyEvent
        key_data = event.data
        if not isinstance(key_data, KeyEvent):
            return

        key_name = key_data.key.lower()
        if key_name == "escape":
            logger.info("Escape key pressed; stopping GUI application")
            self.stop()

    def _handle_window_close(self, event: Event) -> None:
        """Handle window close events routed through the GUI bus."""
        target_identifier = event.target
        handled = False

        if target_identifier:
            with self._window_lock:
                for window_id, window in list(self._windows.items()):
                    if target_identifier in {str(window_id), window.title}:
                        handled = True
                        self.destroy_window(window)
                        break

        if not handled:
            logger.info("Window close event received; stopping GUI runtime")
            self.stop()

    def render_gui_node(self, node: GuiNode, window: Any | None = None) -> None:
        """Render a GUI node to a window."""
        if window is None:
            # Use first available window
            with self._window_lock:
                if self._windows:
                    window = next(iter(self._windows.values()))
                else:
                    logger.warning("No windows available to render GUI node")
                    return

        if window:
            window.render_gui_node(node)

    def _cleanup(self) -> None:
        """Clean up application resources."""
        logger.info("Cleaning up GUI application")

        # Stop render thread
        if self._render_thread and self._render_thread.is_alive():
            self._render_thread.join(timeout=1.0)

        if self._event_subsystem is not None:
            for unsubscribe in self._event_handlers:
                try:
                    unsubscribe()
                except Exception as exc:  # pragma: no cover - defensive
                    logger.debug("Failed to unsubscribe GUI event handler: %s", exc)
            self._event_handlers.clear()
            self._event_subsystem.stop_platform_event_loop()

        # Destroy all windows
        with self._window_lock:
            windows = list(self._windows.values())
            self._windows.clear()

        for window in windows:
            try:
                window.close()
            except Exception as e:
                logger.error(f"Error closing window '{window.title}': {e}")

    @property
    def windows(self) -> list[Any]:
        """Get list of active windows."""
        with self._window_lock:
            return list(self._windows.values())

    def __enter__(self) -> GuiApplication:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: type[BaseException], exc_val: BaseException, exc_tb: Traceback) -> None:
        """Context manager exit."""
        self._cleanup()


def create_application(backend: str = "auto") -> GuiApplication:
    """Create a new GUI application."""
    return GuiApplication(backend)


_default_application: GuiApplication | None = None


def get_default_application() -> GuiApplication:
    """Get or create the default GUI application."""
    global _default_application
    if _default_application is None:
        _default_application = GuiApplication()
    return _default_application
