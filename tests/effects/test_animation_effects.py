"""Tests for concrete animation effect classes."""

from __future__ import annotations

import types

import pytest

from ornata.api.exports.effects import (
    FadeInAnimation,
    GradientPulseAnimation,
    ParticleTrailAnimation,
    PulseAnimation,
    ShakeAnimation,
    TypewriterAnimation,
    WaveAnimation,
)
from ornata.definitions.dataclasses.components import Component

import ornata.effects.animation.effects as effects_module


def _component(name: str = "AnimNode") -> Component:
    return Component(component_name=name)


def _stub_palette(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyPalette:
        @staticmethod
        def get_effect(name: str) -> str:
            return f"<{name}>"

    monkeypatch.setattr(effects_module, "PaletteLibrary", DummyPalette)
    monkeypatch.setattr(effects_module, "resolve_color", lambda value: f"color:{value}")
    monkeypatch.setattr(effects_module, "render_gradient", lambda text, start, end: f"grad[{text}:{start}->{end}]")


def test_typewriter_animation_builds_colored_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """TypewriterAnimation should update ``current_text`` with palette formatting."""

    _stub_palette(monkeypatch)
    animation = TypewriterAnimation(_component("Writer"), text="Hello", delay=0.01, color="blue")
    animation.start()
    animation.update(animation.duration)

    state = animation.get_current_state()
    assert state.transforms
    current_text = state.transforms[0].current_text or ""
    assert "Hello" in current_text
    assert "color:blue" in current_text


def test_fade_and_pulse_animation_progress() -> None:
    """FadeInAnimation and PulseAnimation should expose opacity transforms."""

    fade = FadeInAnimation(_component("Fade"), steps=4, delay=0.01)
    fade.start()
    fade.update(0.02)
    fade_state = fade.get_current_state()
    assert fade_state.transforms
    assert fade_state.transforms[0].opacity > 0.0

    pulse = PulseAnimation(_component("Pulse"), cycles=1, delay=0.01)
    pulse.start()
    pulse.update(0.02)
    pulse_state = pulse.get_current_state()
    assert pulse_state.transforms
    assert 0.0 <= pulse_state.transforms[0].opacity <= 1.0


def test_wave_and_shake_animation_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    """WaveAnimation and ShakeAnimation should populate positions/offset metadata."""

    monkeypatch.setattr(effects_module.math, "sin", lambda value: 0.0)
    wave = WaveAnimation(_component("Wave"), text="ABC", cycles=1, delay=0.01)
    wave.start()
    wave.update(0.05)
    wave_state = wave.get_current_state()
    assert wave_state.transforms
    assert wave_state.transforms[0].positions == [1, 1, 1]

    monkeypatch.setattr(effects_module.random, "randint", lambda _a, _b: 2)
    shake = ShakeAnimation(_component("Shake"), text="!!")
    shake.start()
    shake.update(0.02)
    shake_state = shake.get_current_state()
    assert shake_state.transforms
    assert shake_state.transforms[0].offset == "  "


def test_gradient_pulse_animation_blends(monkeypatch: pytest.MonkeyPatch) -> None:
    """GradientPulseAnimation should set gradient text using palette helpers."""

    _stub_palette(monkeypatch)
    animation = GradientPulseAnimation(_component("Gradient"), text="RGB", duration=0.1)
    animation.start()
    animation.update(0.05)
    state = animation.get_current_state()
    assert state.transforms
    gradient_text = state.transforms[0].gradient_text or ""
    assert gradient_text.startswith("grad[")


def test_particle_trail_animation_builds_overlay(monkeypatch: pytest.MonkeyPatch) -> None:
    """ParticleTrailAnimation should generate overlay text with palette helpers."""

    _stub_palette(monkeypatch)

    def fake_random() -> float:
        return 0.4

    rng = types.SimpleNamespace(randint=lambda _a, _b: 1, random=fake_random)
    monkeypatch.setattr(effects_module, "random", rng)

    animation = ParticleTrailAnimation(_component("Trail"), text="trace", trail_length=3)
    animation.start()
    animation.update(0.1)
    state = animation.get_current_state()
    assert state.transforms
    trail_text = state.transforms[0].trail_text or ""
    assert "trace" in trail_text
