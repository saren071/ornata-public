"""Predefined particle effects with configuration factories."""

from __future__ import annotations

import threading
from typing import Any

from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


class ParticleEffects:
    """Factory for creating predefined particle effects with proper configurations.

    Provides high-level interfaces for creating common particle effects like explosions,
    fireworks, weather effects, and other visual phenomena. Each effect is configured
    with appropriate physics, rendering, and emission parameters.
    """

    def __init__(self) -> None:
        """Initialize particle effects factory with thread-safe operations."""
        self._lock = threading.RLock()
        logger.debug("Initialized particle effects factory")

    def create_explosion(self, position: tuple[float, float], intensity: float = 1.0) -> dict[str, dict[str, Any]]:
        """Create an explosion particle effect.

        Args:
            position: Center position of the explosion.
            intensity: Explosion intensity multiplier (affects particle count and speed).

        Returns:
            Configuration dictionary for explosion effect.
        """
        with self._lock:
            config: dict[str, Any] = {
                "position": position,
                "emission_rate": int(50 * intensity),
                "max_particles": int(100 * intensity),
                "lifetime": 1.5,
                "speed": (0.0, 0.0),
                "speed_variation": 50.0 * intensity,
                "size": 2.0,
                "size_variation": 1.0,
                "color": (255, 100, 0, 255),  # Orange
                "color_variation": 50,
                "physics": {
                    "gravity": (0.0, 100.0),
                    "damping": 0.1,
                    "bounce": 0.0,
                    "friction": 0.0
                }
            }
            logger.debug(f"Created explosion effect at {position} with intensity {intensity}")
            return config

    def create_firework(self, position: tuple[float, float], colors: list[tuple[int, int, int, int]] | None = None) -> dict[str, Any]:
        """Create a firework particle effect.

        Args:
            position: Launch position of the firework.
            colors: Optional list of colors for the firework burst. Uses defaults if None.

        Returns:
            Configured ParticleSystemConfig for firework effect.
        """

        with self._lock:
            if colors is None:
                colors = [
                    (255, 0, 0, 255),  # Red
                    (0, 255, 0, 255),  # Green
                    (0, 0, 255, 255),  # Blue
                    (255, 255, 0, 255),  # Yellow
                    (255, 0, 255, 255),  # Magenta
                ]

            # Use first color as base, store others in renderer config
            base_color = colors[0] if colors else (255, 255, 255, 255)

            config = {
                "position": position,
                "emission_rate": 200,
                "max_particles": 300,
                "lifetime": 3.0,
                "speed": (0.0, -100.0),  # Upward launch
                "speed_variation": 20.0,
                "size": 1.5,
                "size_variation": 0.5,
                "color": base_color,
                "color_variation": 50,
                "physics": {
                    "gravity": (0.0, 50.0),
                    "damping": 0.05,
                    "bounce": 0.0,
                    "friction": 0.0
                },
                "renderer": {
                    "firework_colors": colors,
                    "burst_pattern": "radial"
                }
            }
            logger.debug(f"Created firework effect at {position} with {len(colors)} colors")
            return config

    def create_rain(self, area: tuple[float, float, float, float], intensity: float = 1.0) -> dict[str, Any]:
        """Create a rain particle effect.

        Args:
            area: Rain area as (x, y, width, height).
            intensity: Rain intensity multiplier.

        Returns:
            Configuration dictionary for rain effect.
        """
        with self._lock:
            x, y, width, _ = area
            config = {
                "position": (x + width / 2, y),
                "emission_rate": int(100 * intensity),
                "max_particles": int(500 * intensity),
                "lifetime": 5.0,
                "speed": (0.0, 200.0),
                "speed_variation": 50.0,
                "size": 0.5,
                "size_variation": 0.2,
                "color": (100, 150, 255, 180),  # Light blue
                "color_variation": 20,
                "physics": {
                    "gravity": (0.0, 0.0),  # Constant downward speed
                    "damping": 0.0,
                    "bounce": 0.0,
                    "friction": 0.0,
                    "bounds": area,
                    "wrap_around": True,
                }
            }
            logger.debug(f"Created rain effect in area {area} with intensity {intensity}")
            return config

    def create_snow(self, area: tuple[float, float, float, float], intensity: float = 1.0) -> dict[str, Any]:
        """Create a snow particle effect.

        Args:
            area: Snow area as (x, y, width, height).
            intensity: Snow intensity multiplier.

        Returns:
            Configuration dictionary for snow effect.
        """
        with self._lock:
            x, y, width, _ = area
            config = {
                "position": (x + width / 2, y),
                "emission_rate": int(50 * intensity),
                "max_particles": int(200 * intensity),
                "lifetime": 10.0,
                "speed": (0.0, 30.0),
                "speed_variation": 20.0,
                "size": 1.0,
                "size_variation": 0.5,
                "color": (255, 255, 255, 200),  # White
                "color_variation": 10,
                "physics": {
                    "gravity": (0.0, 0.0),
                    "damping": 0.0,
                    "bounce": 0.0,
                    "friction": 0.0,
                    "bounds": area,
                    "wrap_around": True
                }
            }
            logger.debug(f"Created snow effect in area {area} with intensity {intensity}")
            return config

    def create_smoke(self, position: tuple[float, float], intensity: float = 1.0) -> dict[str, Any]:
        """Create a smoke particle effect.

        Args:
            position: Source position of the smoke.
            intensity: Smoke intensity multiplier.

        Returns:
            Configuration dictionary for smoke effect.
        """
        with self._lock:
            config = {
                "position": position,
                "emission_rate": int(20 * intensity),
                "max_particles": int(100 * intensity),
                "lifetime": 4.0,
                "speed": (0.0, -20.0),
                "speed_variation": 10.0,
                "size": 3.0,
                "size_variation": 1.0,
                "color": (100, 100, 100, 100),  # Gray
                "color_variation": 30,
                "physics": {
                    "gravity": (0.0, -10.0),  # Slight upward drift
                    "damping": 0.1,
                    "bounce": 0.0,
                    "friction": 0.0,
                }
            }
            logger.debug(f"Created smoke effect at {position} with intensity {intensity}")
            return config
