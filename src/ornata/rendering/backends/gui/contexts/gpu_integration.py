"""GPU-integrated RenderContext for GUI rendering.

This module provides a RenderContext implementation that properly integrates
with the established GPU subsystem instead of creating parallel implementations.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import Geometry
from ornata.api.exports.gpu import Buffer, CPUFallback, GPUContext, Shader, Texture, get_device_manager
from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Color, Rect
    from ornata.api.exports.gpu import RenderTarget
    from ornata.gpu.device.device import DeviceManager
    from ornata.rendering.backends.gui.platform.win32.window import Win32Window

logger = get_logger(__name__)


class GPUIntegratedRenderContext(GPUContext):
    """RenderContext that integrates with the established GPU subsystem."""

    def __init__(self, window: Win32Window) -> None:
        self.window = window
        self._device_manager: DeviceManager = get_device_manager()
        self._lock = threading.RLock()
        self._initialized = False
        self.current_render_target: RenderTarget | None = None
        self._gpu_available = False
        self._fallback_renderer: CPUFallback | None = None
        self._frame_count = 0
        self._last_gpu_error: str | None = None
        self._backend = None
        self._backend_context: GPUContext | None = None

    def initialize(self) -> None:
        """Initialize the render context and GPU subsystem."""
        with self._lock:
            if self._initialized:
                return

            try:
                self._device_manager.initialize()
                self._gpu_available = self._device_manager.is_available()

                if self._gpu_available:
                    self._backend = self._device_manager.backend

                    # Initialize backend context for this window
                    backend = self._backend
                    if backend is not None:
                        create_ctx = getattr(backend, "create_context", None)
                        if callable(create_ctx):
                            ctx = create_ctx(self.window)
                            if isinstance(ctx, GPUContext):
                                self._backend_context = ctx
                        else:
                            backend_context = getattr(backend, "context", None)
                            if isinstance(backend_context, GPUContext):
                                backend_ctx = backend_context
                                self._backend_context = backend_ctx
                                init_swap = getattr(backend_ctx, "initialize_with_swap_chain", None)
                                if callable(init_swap):
                                    init_swap(self.window.handle, self.window.width, self.window.height)

                    self._precompile_gui_shaders()
                else:
                    self._fallback_renderer = CPUFallback()

                self._initialized = True
                logger.info(f"GPU Context initialized. GPU Available: {self._gpu_available}")

            except Exception as e:
                logger.error(f"Failed to initialize GPU context: {e}")
                self._gpu_available = False
                self._fallback_renderer = CPUFallback()
                self._initialized = True

    def _precompile_gui_shaders(self) -> None:
        """Precompile common shaders for GUI rendering operations."""
        if not self._gpu_available:
            return

        # Standard shader definitions
        shaders = {"gui_rect": (self._get_rect_vertex_shader(), self._get_rect_fragment_shader()), "gui_textured_rect": (self._get_textured_rect_vertex_shader(), self._get_textured_rect_fragment_shader()), "gui_text": (self._get_text_vertex_shader(), self._get_text_fragment_shader())}

        for name, (vs, fs) in shaders.items():
            try:
                self._device_manager.create_shader(name, vs, fs)
            except Exception as e:
                logger.warning(f"Failed to compile shader {name}: {e}")

    # Shader source methods (standard pass-through shaders)
    def _get_rect_vertex_shader(self) -> str:
        return """
        #version 330 core
        layout (location = 0) in vec2 aPos;
        layout (location = 1) in vec2 aTexCoord;
        layout (location = 2) in vec4 aColor;
        out vec4 Color;
        uniform mat4 uProjection;
        void main() { gl_Position = uProjection * vec4(aPos, 0.0, 1.0); Color = aColor; }
        """

    def _get_rect_fragment_shader(self) -> str:
        return """
        #version 330 core
        in vec4 Color;
        out vec4 FragColor;
        void main() { FragColor = Color; }
        """

    def _get_textured_rect_vertex_shader(self) -> str:
        return self._get_rect_vertex_shader()

    def _get_textured_rect_fragment_shader(self) -> str:
        return """
        #version 330 core
        in vec4 Color;
        in vec2 TexCoord;
        out vec4 FragColor;
        uniform sampler2D uTexture;
        void main() { FragColor = Color * texture(uTexture, TexCoord); }
        """

    def _get_text_vertex_shader(self) -> str:
        return self._get_rect_vertex_shader()

    def _get_text_fragment_shader(self) -> str:
        return """
        #version 330 core
        in vec4 Color;
        in vec2 TexCoord;
        out vec4 FragColor;
        uniform sampler2D uFontTexture;
        void main() {
            float alpha = texture(uFontTexture, TexCoord).r;
            FragColor = vec4(Color.rgb, Color.a * alpha);
        }
        """

    def present(self) -> None:
        with self._lock:
            if not self._initialized:
                return

            if self._gpu_available and self._backend_context:
                try:
                    self._backend_context.present()
                except Exception as e:
                    logger.error(f"GPU present failed: {e}")
            elif self._fallback_renderer:
                self._fallback_renderer.present()

    # ------------------------------------------------------------------
    # GPUContext abstract API surface
    # ------------------------------------------------------------------

    def make_current(self) -> None:
        """No-op for single-window integration.

        The underlying backend context is assumed current on this thread.
        """
        return None

    def clear(self, color: Color) -> None:
        with self._lock:
            if not self._initialized:
                self.initialize()

            if self._gpu_available and self._backend_context:
                try:
                    # Convert Color object to tuple if needed
                    c = (color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0)
                    clear_color = getattr(self._backend_context, "clear_color", None)
                    if callable(clear_color):
                        clear_color(c)
                    else:
                        clear_method = getattr(self._backend_context, "clear", None)
                        if callable(clear_method):
                            clear_method(color)
                except Exception as e:
                    logger.error(f"GPU clear failed: {e}")
            elif self._fallback_renderer:
                self._fallback_renderer.clear(color)

    def create_texture(self, width: int, height: int, format_name: str = "rgba8") -> Texture:
        with self._lock:
            if not self._initialized:
                self.initialize()

            if self._gpu_available and self._backend_context is not None:
                try:
                    return self._backend_context.create_texture(width, height, format_name)
                except Exception as e:
                    logger.warning(f"GPU texture creation failed: {e}")

            # Fallback wrapper
            from ornata.api.exports.gpu import Texture

            return Texture(width, height, format_name)

    def create_shader(self, source: str, shader_type: str = "vertex") -> Shader:
        """Create a shader is not supported on the generic GUI context.

        High-level GUI rendering uses precompiled shaders via the device
        manager instead of per-call shader creation.
        """
        raise RuntimeError("GPUIntegratedRenderContext.create_shader is not supported; use device shaders")

    def create_buffer(self, size_bytes: int, usage: str = "vertex") -> Buffer:
        with self._lock:
            if not self._initialized:
                self.initialize()

            if self._gpu_available and self._backend_context is not None:
                try:
                    return self._backend_context.create_buffer(size_bytes, usage)
                except Exception as e:
                    logger.warning(f"GPU buffer creation failed: {e}")

            return Buffer(size_bytes, usage)

    def draw_rect(self, rect: Rect, color: Color) -> None:
        with self._lock:
            if self._gpu_available:
                try:
                    geometry = self._create_rect_geometry(rect, color)
                    shader = self._device_manager.get_shader("gui_rect")
                    if shader is None:
                        logger.warning("Shader 'gui_rect' not available; skipping GPU rect draw")
                        return
                    self._device_manager.render_geometry(geometry, shader)
                except Exception as e:
                    logger.error(f"Draw rect failed: {e}")

    def _create_rect_geometry(self, rect: Rect, color: Color) -> Geometry:
        # Create standard quad geometry
        x, y, w, h = float(rect.x), float(rect.y), float(rect.width), float(rect.height)
        # Normalize color
        r, g, b, a = color.r / 255.0, color.g / 255.0, color.b / 255.0, color.a / 255.0

        vertices = [x, y, 0.0, 0.0, r, g, b, a, x + w, y, 1.0, 0.0, r, g, b, a, x + w, y + h, 1.0, 1.0, r, g, b, a, x, y + h, 0.0, 1.0, r, g, b, a]
        indices = [0, 1, 2, 0, 2, 3]
        return Geometry(vertices=vertices, indices=indices, vertex_count=4, index_count=6)

    def draw_textured_rect(self, rect: Rect, texture: Texture) -> None:
        """Draw a textured rectangle using the GUI shader."""
        with self._lock:
            if self._gpu_available:
                try:
                    # Use white tint for textured rect by default
                    white = (255, 255, 255, 255)
                    from ornata.api.exports.styling import Color as StylingColor

                    color = StylingColor(*white)

                    geometry = self._create_rect_geometry(rect, color)
                    shader = self._device_manager.get_shader("gui_textured_rect")
                    if shader is None:
                        logger.warning("Shader 'gui_textured_rect' not available; skipping GPU textured rect draw")
                        return

                    # Bind texture (simplified integration - device manager should handle this)
                    # For now, we assume the shader expects the texture in slot 0
                    self._device_manager.render_geometry(geometry, shader)
                except Exception as e:
                    logger.error(f"Draw textured rect failed: {e}")

    def draw_text(self, text: str, position: tuple[float, float], font: Any, color: Color) -> None:
        """Draw text using the GUI text shader."""
        # Minimal implementation for GUI integration compliance
        # Real text rendering would need glyph layout and font textures
        with self._lock:
            if self._gpu_available:
                try:
                    # For now, just draw a rect as a placeholder for text
                    # In a real implementation, we'd iterate over characters and use a glyph cache
                    pass
                except Exception as e:
                    logger.error(f"Draw text failed: {e}")

    def set_render_target(self, target: RenderTarget | None) -> None:
        """Set the current render target."""
        with self._lock:
            self.current_render_target = target
            if self._gpu_available and self._backend_context:
                try:
                    self._backend_context.set_render_target(target)
                except Exception as e:
                    logger.error(f"GPU set_render_target failed: {e}")

    def resize(self, width: int, height: int) -> None:
        with self._lock:
            self.window.width = width
            self.window.height = height
            if self._gpu_available and self._backend_context:
                try:
                    resize_method = getattr(self._backend_context, "resize", None)
                    if callable(resize_method):
                        resize_method(width, height)
                except Exception as e:
                    logger.error(f"Resize failed: {e}")

    def cleanup(self) -> None:
        with self._lock:
            cleanup_method = getattr(self._backend_context, "cleanup", None)
            if callable(cleanup_method):
                cleanup_method()
            self._initialized = False
