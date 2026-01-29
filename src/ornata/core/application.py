"""High-level Application wrapper for public Ornata usage."""

from __future__ import annotations

import builtins
import sys
import time
from typing import TYPE_CHECKING, Any

from ornata.api.exports.rendering import (
    ANSIRenderer,
    GuiApplication,
    TerminalApp,
    TerminalSession,
    TTYRenderer,
    create_cli_input_pipeline,
)
from ornata.api.exports.rendering import (
    get_runtime as get_gui_runtime,
)
from ornata.core.runtime import OrnataRuntime
from ornata.definitions.dataclasses.core import AppConfig, RuntimeFrame
from ornata.definitions.dataclasses.rendering import BackendTarget
from ornata.utils import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable
    from threading import Thread

    from ornata.api.exports.definitions import RenderOutput, VDOMRendererContext, VDOMTree
    from ornata.api.exports.events import EventSubsystem
    from ornata.definitions.dataclasses.components import Component
    from ornata.definitions.dataclasses.rendering import GuiNode
    from ornata.rendering.backends.cli.input import CLIInputPipeline
    from ornata.rendering.core.base_renderer import Renderer


def register_backend_with_bridge(backend_target: BackendTarget, renderer: Renderer) -> VDOMRendererContext:
    """
    Register `renderer` with the global VDOM bridge.

    ### Parameters
    
    * **backend_target** (`BackendTarget`): Backend for which the renderer is being registered.
    * **renderer** (`Renderer`): Renderer instance to integrate with the bridge.

    ### Returns
    
    * `VDOMRendererContext`: Context object managed by the VDOM bridge.

    ### See Also
    
    * [get_vdom_renderer_bridge](ornata.rendering.vdom_bridge)
    * `ornata.rendering.vdom_bridge.VDOMRendererBridge.register_renderer`
    """

    from ornata.rendering.vdom_bridge import get_vdom_renderer_bridge

    bridge = get_vdom_renderer_bridge()
    return bridge.register_renderer(backend_target, renderer)


def render_vdom_tree_bridge(vdom_tree: VDOMTree, backend_target: BackendTarget) -> object:
    """
    Render a VDOM tree through the global VDOM bridge.

    ### Parameters
    
    * **vdom_tree** (`VDOMTree`): VDOM tree produced by the runtime.
    * **backend_target** (`BackendTarget`): Backend for which the tree should be rendered.

    ### Returns
    
    * `object`: Renderer-specific output produced by the bridge.

    ### See Also
    
    * [get_vdom_renderer_bridge](ornata.rendering.vdom_bridge)
    * `ornata.rendering.vdom_bridge.VDOMRendererBridge.render_vdom_tree`
    """

    from ornata.rendering.vdom_bridge import get_vdom_renderer_bridge

    bridge = get_vdom_renderer_bridge()
    return bridge.render_vdom_tree(vdom_tree, backend_target)


def print(value: object = "", *args: Any, **kwargs: Any) -> None:
    """
    Proxy the built-in `print` so tests can monkeypatch terminal output.

    ### Parameters
    
    * **value** (`object`, optional): Primary object to print, by default an empty string.
    * **args** (`object`): Additional positional arguments forwarded to `builtins.print`.
    * **kwargs** (`object`): Keyword arguments forwarded to `builtins.print`.

    ### Returns
    
    * `None`: This function does not return a value.

    ### See Also
    
    * `builtins.print`
    """

    builtins.print(value, *args, **kwargs)


class Application:
    """
    Entry point for developers building Ornata applications.

    # Overview
    
    The `Application` class acts as the central coordinator for an Ornata app. 
    It manages the lifecycle, configuration, rendering loop, and event subsystem.

    ### Attributes
    
    * **config** (`AppConfig`): The active configuration object for this application instance.

    ### Usage
    
    ```python
    from ornata import Application

    app = Application()
    
    # Define and mount a component
    @app.mount
    def MyRoot():
        return ...

    # Start the app
    app.run()
    ```
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        """
        Initialize an Ornata application instance with optional configuration.

        Creates a new application instance and sets up the core runtime environment,
        including backend renderers, event handling, and rendering subsystems. The
        application will use default configuration if none is provided.

        ### Parameters
        
        * **config** (`AppConfig | None`, optional): Application configuration object containing runtime settings, backend preferences, and rendering options. If `None`, a default `AppConfig` instance will be created automatically.

        ### Raises
        
        * `TypeError`: If `config` is provided but is not an instance of `AppConfig` or `None`.
        * `RuntimeError`: If the runtime environment fails to initialize properly.
        * `ImportError`: If required backend dependencies are missing and cannot be loaded.

        ### Notes
        
        The initialization process performs the following steps:
        
        1. Validates and stores the configuration object.
        2. Creates the core runtime environment.
        3. Initializes the logging subsystem.
        4. Prepares backend renderer dictionaries (empty until backends are registered).
        5. Sets default render loop parameters (30 FPS target).
        
        The application instance is not immediately running after initialization.
        You must call the appropriate `run` or `run_loop` methods to begin execution.

        Backend renderers are lazily initialized when first used, not during `__init__`. 
        This allows for faster startup and reduces memory overhead.

        ### Examples
        
        Create an application with default configuration:
        
        ```python
        app = Application()
        app.run()
        ```
        
        Create an application with custom configuration:
        
        ```python
        config = AppConfig(backend=BackendTarget.TERMINAL, debug=True)
        app = Application(config)
        app.run()
        ```
        
        Access application configuration after initialization:
        
        ```python
        app = Application()
        print(app.config.backend)
        # Output: BackendTarget.TERMINAL
        ```

        ### See Also
        
        * [AppConfig](ornata.definitions.dataclasses.core.AppConfig)
        * [OrnataRuntime](ornata.core.runtime.OrnataRuntime)
        """

        self._config = config or AppConfig()
        self._runtime = OrnataRuntime(self._config)
        self._builder: Callable[[], Component] | None = None
        self._logger = get_logger(__name__)
        self._current_root: Component | None = None
        self._backend_instances: dict[BackendTarget, Renderer] = {}
        self._backend_contexts: dict[BackendTarget, VDOMRendererContext] = {}
        self._last_output: RenderOutput | None = None
        self._loop_interval = 1.0 / 30.0
        self._loop_mode = False
        self._running = False
        self._event_subsystem: EventSubsystem | None = None
        self._cli_input_pipeline: CLIInputPipeline | None = None
        self._cli_terminal_session: TerminalSession | None = None
        self._gui_driver: _GUIRenderDriver | None = None
        self._event_loop_started = False

    @property
    def config(self) -> AppConfig:
        """
        Return the mutable application configuration.

        ### Returns
        
        * `AppConfig`: Mutable application configuration object.

        ### See Also
        
        * [AppConfig](ornata.definitions.dataclasses.core.AppConfig)
        """

        return self._config

    def set_backend(self, backend: BackendTarget) -> None:
        """
        Update the target backend and recreate the runtime.

        ### Parameters
        
        * **backend** (`BackendTarget`): Target backend for the application.

        ### Returns
        
        * `None`

        ### See Also
        
        * [BackendTarget](ornata.definitions.dataclasses.rendering.BackendTarget)
        """

        if self._config.backend is backend:
            return
        self._config.backend = backend
        self._runtime = OrnataRuntime(self._config)
        for stylesheet in self._config.stylesheets:
            self._runtime.load_stylesheet(stylesheet)
        self._backend_instances.clear()
        self._backend_contexts.clear()
        self._last_output = None
        self._logger.info("Backend switched to %s", backend.value)

    def add_stylesheet(self, path: str) -> None:
        """
        Register an OST stylesheet for the application.

        ### Parameters
        
        * **path** (`str`): Filesystem path to the OST stylesheet.

        ### Returns
        
        * `None`

        ### See Also
        
        * `OrnataRuntime.load_stylesheet`
        """

        if path in self._config.stylesheets:
            return
        self._config.stylesheets.append(path)
        self._runtime.load_stylesheet(path)

    def mount(self, component_or_factory: Component | Callable[[], Component]) -> None:
        """
        Register a root component or factory for the application.

        ### Parameters
        
        * **component_or_factory** (`Component | Callable[[], Component]`): 
          Root component instance or a factory function that returns the root component.

        ### Returns
        
        * `None`

        ### See Also
        
        * `OrnataRuntime.run`
        """

        if callable(component_or_factory):
            self._builder = component_or_factory
        else:
            self._builder = lambda component=component_or_factory: component

    def run(self) -> RuntimeFrame:
        """
        Build the component tree, orchestrate a single frame, and drive the active backend.

        This method performs a "one-shot" render.

        ### Returns
        
        * `RuntimeFrame`: The final runtime frame produced by the render cycle.

        ### Raises
        
        * `RuntimeError`: If no component tree is registered. Call `mount()` first.
        """

        if self._builder is None:
            raise RuntimeError("No component tree registered. Call mount() first.")
        component = self._builder()
        self._current_root = component
        self._logger.info("Starting application '%s'", self._config.title)
        frame = self._runtime.run(component)
        self._loop_mode = False
        self._render_frame(frame, loop_mode=False)
        return frame

    def run_loop(self, *, fps: float = 30.0) -> None:
        """
        Continuously build, render, and process events until stopped.

        ### Parameters
        
        * **fps** (`float`, optional): Target frames per second. Default is 30.0.

        ### Returns
        
        * `None`

        ### Raises
        
        * `RuntimeError`: If no component tree is registered. Call `mount()` first.
        * `ValueError`: If `fps` is less than or equal to zero.
        """

        if self._builder is None:
            raise RuntimeError("No component tree registered. Call mount() first.")
        if fps <= 0:
            raise ValueError("fps must be greater than zero")

        self._loop_interval = 1.0 / float(fps)
        self._loop_mode = True
        backend = self._config.backend
        if backend is BackendTarget.CLI:
            self._logger.info("Starting application loop at %.1f FPS", fps)
            self._run_cli_terminal_loop(fps)
            return

        subsystem = self._ensure_event_subsystem()
        if not self._event_loop_started:
            subsystem.start_platform_event_loop()
            self._event_loop_started = True

        if backend is BackendTarget.TTY:
            self._start_cli_input_pipeline(subsystem)
        elif backend is BackendTarget.GUI:
            self._ensure_gui_driver(self._resolve_gui_backend_name(backend), loop_mode=True)

        self._running = True
        self._logger.info("Starting application loop at %.1f FPS", fps)

        try:
            while self._running:
                component = self._builder()
                self._current_root = component
                frame = self._runtime.run(component)
                self._render_frame(frame, loop_mode=True)
                subsystem.pump_platform_events()
                time.sleep(self._loop_interval)
        except KeyboardInterrupt:
            self._logger.info("Application loop interrupted by user")
        finally:
            self.stop()

    def stop(self) -> None:
        """
        Request the currently running application loop to stop.

        Signals the event loop to terminate gracefully at the end of the current cycle.

        ### Returns
        
        * `None`
        """

        self._running = False
        self._loop_mode = False
        if self._cli_input_pipeline is not None:
            self._cli_input_pipeline.stop()
            self._cli_input_pipeline = None
        session = self._cli_terminal_session
        if session is not None:
            session.stop()
            self._cli_terminal_session = None
        if self._event_loop_started and self._event_subsystem is not None:
            self._event_subsystem.stop_platform_event_loop()
            self._event_loop_started = False
        if self._gui_driver is not None:
            self._gui_driver.shutdown()
            self._gui_driver = None

    def _render_frame(self, frame: RuntimeFrame, *, loop_mode: bool) -> None:
        """
        Dispatch the runtime frame to the active backend renderer.

        ### Parameters
        
        * **frame** (`RuntimeFrame`): Runtime frame to dispatch.
        * **loop_mode** (`bool`): Whether the frame is being rendered in loop mode.

        ### Returns
        
        * `None`
        """

        backend = self._config.backend
        if backend is BackendTarget.CLI:
            self._logger.debug("Application._render_frame: dispatching frame to CLI terminal session")
            self._run_terminal_session(
                frame,
                BackendTarget.CLI,
                self._create_cli_renderer,
                loop_mode=loop_mode,
            )
            return

        if backend is BackendTarget.TTY:
            self._logger.debug("Application._render_frame: dispatching frame to TTY terminal session")
            self._run_terminal_session(
                frame,
                BackendTarget.TTY,
                self._create_tty_renderer,
                loop_mode=loop_mode,
            )
            return

        if backend is BackendTarget.GUI:
            backend_name = self._resolve_gui_backend_name(backend)
            self._run_gui_session(frame, backend_name, loop_mode=loop_mode)
            return

        self._logger.warning("Backend '%s' rendering not implemented", backend.value)

    def _run_terminal_session(
        self,
        frame: RuntimeFrame,
        backend_target: BackendTarget,
        factory: Callable[[BackendTarget], Renderer],
        *,
        loop_mode: bool,
    ) -> None:
        """
        Render the current frame to a terminal output device.

        ### Parameters
        
        * **frame** (`RuntimeFrame`): Runtime frame to dispatch.
        * **backend_target** (`BackendTarget`): Target backend for the application.
        * **factory** (`Callable[[BackendTarget], Renderer]`): Factory function to create the renderer.
        * **loop_mode** (`bool`): Whether the frame is being rendered in loop mode.

        ### Returns
        
        * `None`
        """

        self._logger.info(
            "run_terminal_session: backend=%s loop_mode=%s", backend_target.value, loop_mode
        )
        output, previous_content = self._render_terminal_output(
            frame,
            backend_target,
            factory,
        )
        self._display_terminal_output(output, loop_mode=loop_mode, previous_content=previous_content)

    def _run_gui_session(self, frame: RuntimeFrame, backend_name: str, *, loop_mode: bool) -> None:
        """
        Render the current frame using the GUI backend.

        ### Parameters
        
        * **frame** (`RuntimeFrame`): Runtime frame to dispatch.
        * **backend_name** (`str`): Name of the GUI backend to use.
        * **loop_mode** (`bool`): Whether the frame is being rendered in loop mode.

        ### Returns
        
        * `None`
        """

        try:
            driver = self._ensure_gui_driver(backend_name, loop_mode=loop_mode)
        except Exception as exc:  # pragma: no cover - defensive
            self._logger.error("Failed to initialize GUI backend '%s': %s", backend_name, exc)
            return
        driver.present(frame.gui_tree, blocking=not loop_mode)
        self._last_output = None

    def _ensure_backend(
        self,
        backend_target: BackendTarget,
        factory: Callable[[], Renderer],
    ) -> Renderer:
        """
        Ensure a backend and VDOM context exist for `backend_target`.

        ### Parameters
        
        * **backend_target** (`BackendTarget`): Target backend for the application.
        * **factory** (`Callable[[], Renderer]`): Factory function to create the renderer.

        ### Returns
        
        * `Renderer`: Renderer for the backend.
        """

        backend = self._backend_instances.get(backend_target)
        if backend is None:
            backend = factory()
            self._backend_instances[backend_target] = backend
        self._ensure_backend_context(backend_target, lambda: backend)
        return backend

    def _ensure_backend_context(
        self,
        backend_target: BackendTarget,
        factory: Callable[[], Renderer] | None = None,
    ) -> None:
        """
        Register a renderer with the bridge if not already tracked.

        ### Parameters
        
        * **backend_target** (`BackendTarget`): Target backend for the application.
        * **factory** (`Callable[[], Renderer] | None`, optional): Factory function to create the renderer.

        ### Returns
        
        * `None`
        """

        if backend_target in self._backend_contexts:
            return
        backend = self._backend_instances.get(backend_target)
        if backend is None:
            if factory is None:
                raise ValueError(f"No backend factory provided for {backend_target}")
            backend = factory()
            self._backend_instances[backend_target] = backend
        context = register_backend_with_bridge(backend_target, backend)
        self._backend_contexts[backend_target] = context

    def _prepare_render_tree(self, backend_target: BackendTarget) -> object:
        """
        Convert the runtime VDOM tree for `backend_target`.

        ### Parameters
        
        * **backend_target** (`BackendTarget`): Target backend for the application.

        ### Returns
        
        * `object`: Render tree for the backend.
        """

        self._ensure_backend_context(backend_target)
        vdom_tree = self._runtime.vdom_tree
        return render_vdom_tree_bridge(vdom_tree, backend_target)

    def _display_terminal_output(
        self,
        output: RenderOutput,
        *,
        loop_mode: bool,
        previous_content: str | bytes | None,
    ) -> None:
        """
        Emit terminal content to stdout for CLI/TTY previews.

        ### Parameters
        
        * **output** (`RenderOutput`): Render output to emit.
        * **loop_mode** (`bool`): Whether the frame is being rendered in loop mode.
        * **previous_content** (`str | bytes | None`): Previous content to compare against.

        ### Returns
        
        * `None`
        """
        content = self._coerce_output_text(output)
        if loop_mode and previous_content == content:
            return
        if loop_mode:
            self._clear_terminal()
            print(content, end="", flush=True)
            return
        print(content)

    def _coerce_output_text(self, output: RenderOutput) -> str:
        """Return string content from ``output`` decoding bytes when required.

        ### Parameters
        
        * **output** (`RenderOutput`): Render output that may contain bytes.

        ### Returns
        
        * `str`: Textual content ready for terminal emission.
        """

        content = output.content
        if isinstance(content, bytes):
            return content.decode("utf-8", errors="replace")
        return str(content)

    def _render_terminal_output(
        self,
        frame: RuntimeFrame,
        backend_target: BackendTarget,
        factory: Callable[[BackendTarget], Renderer],
    ) -> tuple[RenderOutput, str | bytes | None]:
        """Render ``frame`` for ``backend_target`` and memoize last output.

        ### Parameters
        
        * **frame** (`RuntimeFrame`): Runtime frame to convert.
        * **backend_target** (`BackendTarget`): Target backend.
        * **factory** (`Callable[[BackendTarget], Renderer]`): Renderer factory.

        ### Returns
        
        * `tuple[RenderOutput, str | bytes | None]`: Latest output and prior content.
        """

        backend = self._ensure_backend(backend_target, lambda: factory(backend_target))
        previous_content: str | bytes | None = None
        if self._last_output is not None:
            previous_content = self._last_output.content
        render_tree = frame.gui_tree
        if render_tree is None:
            render_tree = self._prepare_render_tree(backend_target)
        output = backend.render_tree(render_tree, frame.layout)
        self._last_output = output
        return output, previous_content

    def _run_cli_terminal_loop(self, fps: float) -> None:
        """Drive the CLI backend through the live terminal session."""

        if self._builder is None:
            raise RuntimeError("No component tree registered. Call mount() first.")
        terminal_app = _ApplicationTerminalApp(self)
        self._logger.debug("Terminal app: %s", terminal_app)
        session = TerminalSession(sys.stdout)
        self._logger.debug("Terminal session: %s", session)
        self._cli_terminal_session = session
        self._running = True
        self._loop_mode = True
        self._logger.info("Starting CLI terminal session at %.1f FPS", fps)
        try:
            self._logger.debug("Running CLI terminal session")
            session.run(terminal_app, fps=fps)
            self._logger.info("CLI terminal session ended")
        except KeyboardInterrupt:
            self._logger.info("CLI terminal session interrupted by user")
        finally:
            session.stop()
            self._logger.debug("CLI terminal session stopped")
            self._cli_terminal_session = None
            self._running = False

    def _render_cli_frame_content(self) -> str:
        """Build and render the current CLI frame as string content."""

        if self._builder is None:
            raise RuntimeError("No component tree registered. Call mount() first.")
        component = self._builder()
        self._current_root = component
        frame = self._runtime.run(component)
        output, _ = self._render_terminal_output(frame, BackendTarget.CLI, self._create_cli_renderer)
        return self._coerce_output_text(output)

    @staticmethod
    def _clear_terminal() -> None:
        """
        Clear terminal viewport before re-printing a frame.

        ### Returns
        
        * `None`
        """

        print("\x1b[2J\x1b[H", end="")

    def _create_cli_renderer(self, backend_target: BackendTarget) -> Renderer:
        """
        Create the CLI renderer.

        ### Parameters
        
        * **backend_target** (`BackendTarget`): Target backend for the application.

        ### Returns
        
        * `Renderer`: Renderer for the backend.
        """

        return ANSIRenderer(backend_target)

    def _create_tty_renderer(self, backend_target: BackendTarget) -> Renderer:
        """
        Create the TTY renderer.

        ### Parameters
        
        * **backend_target** (`BackendTarget`): Target backend for the application.

        ### Returns
        
        * `Renderer`: Renderer for the backend.
        """

        return TTYRenderer(backend_target)

    def _resolve_gui_backend_name(self, backend: BackendTarget) -> str:
        """
        Resolve which GUI backend string should be used for driver creation.

        ### Parameters
        
        * **backend** (`BackendTarget`): Target backend for the application.

        ### Returns
        
        * `str`: GUI backend string.
        """

        configured = self._config.capabilities.get("gui_backend")  # Always resolve GUI as it runs with either GPU or CPU fallback automatically
        if isinstance(configured, str) and configured:
            return configured
        return "auto"

    def _ensure_event_subsystem(self) -> EventSubsystem:
        """
        Return (and lazily create) the process event subsystem.

        ### Returns
        
        * `EventSubsystem`: Event subsystem for the process.
        """

        if self._event_subsystem is None:
            from ornata.events.runtime import get_event_subsystem

            self._event_subsystem = get_event_subsystem()
        return self._event_subsystem

    def _start_cli_input_pipeline(self, subsystem: EventSubsystem) -> None:
        """
        Ensure the CLI input pipeline is running for terminal backends.

        ### Parameters
        
        * **subsystem** (`EventSubsystem`): Event subsystem for the process.

        ### Returns
        
        * `None`
        """

        if self._cli_input_pipeline is not None:
            self._logger.debug("CLI input pipeline already active")
            return
        self._logger.info("Starting CLI input pipeline for terminal backends")
        pipeline = create_cli_input_pipeline(subsystem)
        pipeline.start()
        self._cli_input_pipeline = pipeline
        self._logger.info("CLI input pipeline started")

    def _ensure_gui_driver(self, backend_name: str, *, loop_mode: bool) -> _GUIRenderDriver:
        """
        Return the GUI driver, reusing when a loop is active.

        ### Parameters
        
        * **backend_name** (`str`): GUI backend name.
        * **loop_mode** (`bool`): Whether the frame is being rendered in loop mode.

        ### Returns
        
        * `_GUIRenderDriver`: GUI driver for the backend.
        """

        if loop_mode:
            if self._gui_driver is None:
                self._gui_driver = _GUIRenderDriver(self._config, self._logger, backend_name=backend_name)
                self._gui_driver.ensure_running()
            return self._gui_driver
        return _GUIRenderDriver(self._config, self._logger, backend_name=backend_name)


class _GUIRenderDriver:
    """
    Bridges GuiNode snapshots into the GUI runtime.

    ### Parameters
    
    * **config** (`AppConfig`): Application configuration.
    * **logger** (`Any`): Logger for the application.
    * **backend_name** (`str`, optional): GUI backend name, by default "auto".
    """

    def __init__(self, config: AppConfig, logger: Any, *, backend_name: str = "auto") -> None:
        self._logger = logger
        self._config = config
        self._backend_name = backend_name
        self._app = GuiApplication(backend=backend_name)
        self._window = self._app.create_window(config.title, config.viewport_width, config.viewport_height)
        self._runtime = get_gui_runtime()
        if self._runtime is None:
            raise RuntimeError("GUI runtime unavailable")
        self._app_thread: Thread | None = None
        self._loop_active = False

    def present(self, gui_node: GuiNode, *, blocking: bool = True) -> None:
        """
        Render `gui_node` to the active GUI window.

        ### Parameters
        
        * **gui_node** (`GuiNode`): GUI node to render.
        * **blocking** (`bool`, optional): Whether to block until the frame is rendered, by default `True`.

        ### Returns
        
        * `None`
        """

        if self._runtime is None or self._window is None:
            raise RuntimeError("GUI runtime/window not initialized")
        self._runtime.render_gui_node(gui_node, self._window)
        if blocking:
            self._app.run()
            return
        self.ensure_running()

    def ensure_running(self) -> None:
        """
        Ensure the GUI application loop is active.

        ### Returns
        
        * `None`
        """

        if self._app.is_running:
            self._loop_active = True
            return
        self._loop_active = True
        self._app_thread = self._app.run_async()

    def shutdown(self) -> None:
        """
        Stop the GUI application loop and clean up.

        ### Returns
        
        * `None`
        """

        self._loop_active = False
        self._app.stop()
        thread = self._app_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=1.0)
        self._app_thread = None


class _ApplicationTerminalApp(TerminalApp):
    """Adapter that exposes Application renders to TerminalSession."""

    def __init__(self, application: Application) -> None:
        super().__init__()
        self._application = application

    def render(self) -> str:
        """Build and return the latest application frame."""

        return self._application._render_cli_frame_content()

    def on_key(self, key: str) -> None:
        """Handle quit gestures and forward to the Application."""

        super().on_key(key)
        if key.lower() in {"q", "escape", "ctrl+c"}:
            self.should_quit = True


__all__ = [
    "Application",
]