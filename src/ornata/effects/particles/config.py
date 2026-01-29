"""Particle system configuration classes and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ornata.api.exports.definitions import InvalidParticleConfigError
from ornata.api.exports.utils import get_logger

logger = get_logger(__name__)


@dataclass(slots=True, frozen=True)
class ParticleSystemConfig:
    """Configuration for a particle system.

    This class defines all the parameters needed to create and configure
    a particle system, including emission, physics, and rendering settings.

    Attributes:
        position: Initial position of the emitter as (x, y) tuple.
        emission_rate: Number of particles emitted per second.
        max_particles: Maximum number of particles allowed in the system.
        lifetime: Base lifetime of particles in seconds.
        speed: Initial speed as (vx, vy) tuple for directional emission.
        speed_variation: Random variation applied to speed.
        size: Base size of particles.
        size_variation: Random variation applied to size.
        color: Base color as (r, g, b, a) tuple (0-255).
        color_variation: Random variation applied to color components.
        rotation_speed: Base rotation speed in radians per second.
        rotation_variation: Random variation applied to rotation speed.
        physics: Physics configuration dictionary.
        renderer: Renderer-specific configuration dictionary.
    """

    position: tuple[float, float] = (0.0, 0.0)
    emission_rate: float = 10.0
    max_particles: int = 100
    lifetime: float = 2.0
    speed: tuple[float, float] = (0.0, 0.0)
    speed_variation: float = 0.0
    size: float = 1.0
    size_variation: float = 0.0
    color: tuple[int, int, int, int] = (255, 255, 255, 255)
    color_variation: float = 0.0
    rotation_speed: float = 0.0
    rotation_variation: float = 0.0
    physics: dict[str, Any] = field(default_factory=dict)
    renderer: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate configuration parameters."""
        # Position validation
        if len(self.position) != 2:
            raise InvalidParticleConfigError("Position must be a tuple of (x, y)")

        # Emission rate validation
        if self.emission_rate < 0:
            raise InvalidParticleConfigError("Emission rate must be non-negative")

        # Max particles validation
        if self.max_particles <= 0:
            raise InvalidParticleConfigError("Max particles must be positive")

        # Lifetime validation
        if self.lifetime <= 0:
            raise InvalidParticleConfigError("Lifetime must be positive")

        # Speed validation
        if len(self.speed) != 2:
            raise InvalidParticleConfigError("Speed must be a tuple of (vx, vy)")

        # Size validation
        if self.size <= 0:
            raise InvalidParticleConfigError("Size must be positive")

        # Color validation
        if len(self.color) != 4:
            raise InvalidParticleConfigError("Color must be a tuple of (r, g, b, a)")
        for component in self.color:
            if not (0 <= component <= 255):
                raise InvalidParticleConfigError("Color components must be in range 0-255")

        # Variation validations
        if self.speed_variation < 0:
            raise InvalidParticleConfigError("Speed variation must be non-negative")
        if self.size_variation < 0:
            raise InvalidParticleConfigError("Size variation must be non-negative")
        if self.color_variation < 0:
            raise InvalidParticleConfigError("Color variation must be non-negative")
        if self.rotation_variation < 0:
            raise InvalidParticleConfigError("Rotation variation must be non-negative")

    @classmethod
    def for_effect(cls, effect_type: str, **kwargs: Any) -> ParticleSystemConfig:
        """Create a configuration for a predefined effect.

        Args:
            effect_type: Type of effect ("explosion", "firework", "rain", etc.)
            **kwargs: Effect-specific parameters

        Returns:
            Configured ParticleSystemConfig instance

        Raises:
            InvalidParticleConfigError: If effect type is unknown
        """
        from ornata.effects.particles.effects import ParticleEffects

        effects = ParticleEffects()
        if effect_type == "explosion":
            config_dict = effects.create_explosion(
                position=kwargs.get("position", (0.0, 0.0)),
                intensity=kwargs.get("intensity", 1.0)
            )
        elif effect_type == "firework":
            config_dict = effects.create_firework(
                position=kwargs.get("position", (0.0, 0.0)),
                colors=kwargs.get("colors")
            )
        elif effect_type == "rain":
            config_dict = effects.create_rain(
                area=kwargs.get("area", (0.0, 0.0, 100.0, 100.0)),
                intensity=kwargs.get("intensity", 1.0)
            )
        elif effect_type == "snow":
            config_dict = effects.create_snow(
                area=kwargs.get("area", (0.0, 0.0, 100.0, 100.0)),
                intensity=kwargs.get("intensity", 1.0)
            )
        elif effect_type == "smoke":
            config_dict = effects.create_smoke(
                position=kwargs.get("position", (0.0, 0.0)),
                intensity=kwargs.get("intensity", 1.0)
            )
        else:
            raise InvalidParticleConfigError(f"Unknown effect type: {effect_type}")

        return cls.from_dict(config_dict)

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> ParticleSystemConfig:
        """Create configuration from a dictionary.

        Args:
            config: Configuration dictionary

        Returns:
            ParticleSystemConfig instance
        """
        return cls(**config)
