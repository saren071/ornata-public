"""Animation effects migrated from legacy implementation."""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from ornata.api.exports.definitions import AnimationState, Keyframe, Transform
from ornata.api.exports.styling import PaletteLibrary, render_gradient, resolve_color
from ornata.effects.animation.keyframes import Animation

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Component


class TypewriterAnimation(Animation):
    """Typewriter effect animation."""

    def __init__(
        self,
        component: Component,
        text: str,
        delay: float = 0.05,
        color: str | None = None,
    ) -> None:
        """Initialize typewriter animation.

        Args:
            component: The component to animate.
            text: Text to animate.
            delay: Delay between characters.
            color: Text color.
        """
        self.text = text
        self.color = color
        duration = len(text) * delay
        keyframes = [
            Keyframe(offset=0.0, properties={"text_length": 0}),
            Keyframe(offset=1.0, properties={"text_length": len(text)}),
        ]
        super().__init__(component, keyframes, duration)

    def _interpolate_keyframes(self, start: Keyframe, end: Keyframe, progress: float) -> Transform:
        """Interpolate between keyframes.

        Args:
            start: Start keyframe.
            end: End keyframe.
            progress: Interpolation progress.

        Returns:
            Interpolated transform.
        """
        transform = super()._interpolate_keyframes(start, end, progress)
        if "text_length" in start.properties and "text_length" in end.properties:
            start_val = float(start.properties["text_length"])
            end_val = float(end.properties["text_length"])
            transform.text_length = start_val + (end_val - start_val) * progress
        return transform

    def get_current_state(self) -> AnimationState:
        """Get current animation state.

        Returns:
            Current animation state.
        """
        state = super().get_current_state()
        if state.transforms:
            transform = state.transforms[0]
            if hasattr(transform, "text_length"):
                char_count = int(transform.text_length)
                current_text = self.text[:char_count]
                if self.color:
                    resolved_color = resolve_color(self.color)
                    if resolved_color is not None:
                        current_text = resolved_color + current_text + PaletteLibrary.get_effect("reset")
                    else:
                        current_text = current_text + PaletteLibrary.get_effect("reset")
                transform.current_text = current_text
        return state


class FadeInAnimation(Animation):
    """Fade-in effect animation."""

    def __init__(
        self,
        component: Component,
        steps: int = 5,
        delay: float = 0.1,
    ) -> None:
        """Initialize fade-in animation.

        Args:
            component: The component to animate.
            steps: Number of fade steps.
            delay: Delay between steps.
        """
        duration = steps * delay
        keyframes = [
            Keyframe(offset=0.0, properties={"opacity": 0.0}),
            Keyframe(offset=1.0, properties={"opacity": 1.0}),
        ]
        super().__init__(component, keyframes, duration)


class PulseAnimation(Animation):
    """Pulse effect animation."""

    def __init__(
        self,
        component: Component,
        cycles: int = 3,
        delay: float = 0.1,
        color: str = "fg",
    ) -> None:
        """Initialize pulse animation.

        Args:
            component: The component to animate.
            cycles: Number of pulse cycles.
            delay: Delay between pulses.
            color: Text color.
        """
        self.color = color
        duration: float = cycles * 2 * delay
        keyframes: list[Keyframe] = []
        for i in range(cycles * 2):
            offset = i / (cycles * 2)
            opacity = 0.5 if i % 2 == 0 else 1.0
            keyframes.append(Keyframe(offset=offset, properties={"opacity": opacity}))
        keyframes.append(Keyframe(offset=1.0, properties={"opacity": 1.0}))
        super().__init__(component, keyframes, duration)


class WaveAnimation(Animation):
    """Wave effect animation."""

    def __init__(
        self,
        component: Component,
        text: str,
        cycles: int = 1,
        delay: float = 0.05,
        color: str = "fg",
    ) -> None:
        """Initialize wave animation.

        Args:
            component: The component to animate.
            text: Text to animate.
            cycles: Number of wave cycles.
            delay: Delay between frames.
            color: Text color.
        """
        self.text = text
        self.color = color
        duration = len(text) * 4 * cycles * delay
        keyframes = [
            Keyframe(offset=0.0, properties={}),
            Keyframe(offset=1.0, properties={}),
        ]
        super().__init__(component, keyframes, duration)

    def get_current_state(self) -> AnimationState:
        """Get current animation state.

        Returns:
            Current animation state.
        """
        state = super().get_current_state()
        t = state.progress * len(self.text) * 4
        positions: list[int] = []
        for i in range(len(self.text)):
            y = int((math.sin((i + t) / 2.0) + 1) * 1)
            positions.append(y)
        if state.transforms:
            transform = state.transforms[0]
            transform.positions = positions
            transform.color = self.color
        return state


class ShakeAnimation(Animation):
    """Shake effect animation."""

    def __init__(
        self,
        component: Component,
        text: str,
        cycles: int = 8,
        delay: float = 0.04,
        color: str = "fg",
    ) -> None:
        """Initialize shake animation.

        Args:
            component: The component to animate.
            text: Text to animate.
            cycles: Number of shake cycles.
            delay: Delay between shakes.
            color: Text color.
        """
        self.text = text
        self.color = color
        duration = cycles * delay
        keyframes = [
            Keyframe(offset=0.0, properties={}),
            Keyframe(offset=1.0, properties={}),
        ]
        super().__init__(component, keyframes, duration)

    def get_current_state(self) -> AnimationState:
        """Get current animation state.

        Returns:
            Current animation state.
        """
        state = super().get_current_state()
        offset = " " * random.randint(0, 3) if state.progress < 1.0 else ""
        if state.transforms:
            transform = state.transforms[0]
            transform.offset = offset
            transform.color = self.color
        return state


class GradientPulseAnimation(Animation):
    """Gradient pulse effect animation."""

    def __init__(
        self,
        component: Component,
        text: str,
        palette: list[tuple[int, int, int]] | None = None,
        duration: float = 2.0,
        cycles: int = 1,
        fps: int = 24,
    ) -> None:
        """Initialize gradient pulse animation.

        Args:
            component: The component to animate.
            text: Text to animate.
            palette: Color palette for gradient.
            duration: Duration per cycle.
            cycles: Number of cycles.
            fps: Frames per second.
        """
        self.text = text
        self.palette = palette or [(0, 255, 255), (255, 0, 255), (255, 255, 0)]
        self.fps = fps
        total_duration = duration * cycles
        keyframes = [
            Keyframe(offset=0.0, properties={}),
            Keyframe(offset=1.0, properties={}),
        ]
        super().__init__(component, keyframes, total_duration)

    def get_current_state(self) -> AnimationState:
        """Get current animation state.

        Returns:
            Current animation state.
        """
        state = super().get_current_state()
        phase = state.progress
        start_col = self._blend(self.palette, phase)
        end_col = self._blend(self.palette, phase + 0.5)
        gradient_text = render_gradient(self.text, start_col, end_col)
        if state.transforms:
            transform = state.transforms[0]
            transform.gradient_text = gradient_text
        return state

    def _blend(self, colors: list[tuple[int, int, int]], position: float) -> tuple[int, int, int]:
        """Blend colors for gradient.

        Args:
            colors: List of colors.
            position: Position in gradient.

        Returns:
            Blended color.
        """
        if len(colors) == 1:
            return colors[0]
        position = position % 1.0
        segment = position * (len(colors) - 1)
        idx = int(segment)
        frac = segment - idx
        start = colors[idx]
        end = colors[min(idx + 1, len(colors) - 1)]
        r = int(start[0] + (end[0] - start[0]) * frac)
        g = int(start[1] + (end[1] - start[1]) * frac)
        b = int(start[2] + (end[2] - start[2]) * frac)
        return (r, g, b)


class ParticleTrailAnimation(Animation):
    """Particle trail effect animation."""

    def __init__(
        self,
        component: Component,
        text: str,
        duration: float = 2.0,
        fps: int = 30,
        color: str = "cyan",
        glyph: str = "•",
        trail_length: int = 8,
    ) -> None:
        """Initialize particle trail animation.

        Args:
            component: The component to animate.
            text: Text to animate.
            duration: Animation duration.
            fps: Frames per second.
            color: Particle color.
            glyph: Particle glyph.
            trail_length: Length of particle trail.
        """
        self.text = text
        self.fps = fps
        self.color = color
        self.glyph = glyph
        self.trail_length = trail_length
        self.particles: list[tuple[int, int]] = []
        keyframes = [
            Keyframe(offset=0.0, properties={}),
            Keyframe(offset=1.0, properties={}),
        ]
        super().__init__(component, keyframes, duration)

    def update(self, delta_time: float) -> None:
        """Update animation state.

        Args:
            delta_time: Time elapsed since last update.
        """
        super().update(delta_time)
        self.particles = [(position, ttl - 1) for (position, ttl) in self.particles if ttl > 1]
        if random.random() < 0.5:
            self.particles.append((random.randint(0, len(self.text)), self.trail_length))

    def get_current_state(self) -> AnimationState:
        """Get current animation state.

        Returns:
            Current animation state.
        """
        from ornata.api.exports.styling import PaletteLibrary
        state = super().get_current_state()
        overlay = [" "] * (len(self.text) + self.trail_length)
        for pos, _ttl in self.particles:
            idx = min(len(overlay) - 1, pos)
            overlay[idx] = self.glyph
        overlay_text = "".join(overlay).rstrip()
        col = resolve_color(self.color) or ""
        reset = PaletteLibrary.get_effect("reset")
        dim = PaletteLibrary.get_effect("dim")
        trail = (
            f"{col}{self.text}{reset} {dim}{overlay_text}{reset}"
        )
        if state.transforms:
            transform = state.transforms[0]
            transform.trail_text = trail
        return state
