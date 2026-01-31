"""Test that demonstrates complete ResolvedStyle with full backend output."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ornata.definitions.dataclasses.effects import Animation, Keyframe, Keyframes
from ornata.definitions.dataclasses.styling import (
    BackendStylePayload,
    Border,
    BorderRadius,
    BoxShadow,
    ColorLiteral,
    Gradient,
    Insets,
    Length,
    ResolvedStyle,
    StylingContext,
    TextShadow,
    Transition,
)
from ornata.definitions.enums import BackendTarget
from ornata.styling.adapters.cli_mapper import CLIMapper
from ornata.styling.adapters.gui_mapper import GUIMapper
from ornata.styling.runtime.runtime import StylingRuntime


def _cell_metrics() -> tuple[int, int]:
    """Return mock cell metrics (width, height)."""
    return (8, 16)


def _font_metrics() -> tuple[int, int]:
    """Return mock font metrics (ascent, descent)."""
    return (12, 4)


def _get_cli_caps() -> dict[str, Any]:
    """Return CLI capability descriptor."""
    return {
        "color_depth": "C256",
        "dpi": 96,
        "cell_metrics": _cell_metrics,
    }


def _get_gui_caps() -> dict[str, Any]:
    """Return GUI capability descriptor."""
    return {
        "color_depth": "TRUECOLOR",
        "dpi": 96,
        "cell_metrics": _cell_metrics,
        "font_metrics": _font_metrics,
    }


def build_complete_resolved_style() -> ResolvedStyle:
    """Build a ResolvedStyle with comprehensive fields populated.

    Returns:
        ResolvedStyle: A fully populated style for testing mappers.
    """
    style = ResolvedStyle()

    # Colors
    style.color = ColorLiteral(kind="hex", value="#3ea6ff")
    style.background = ColorLiteral(kind="hex", value="#111318")
    style.border_color = ColorLiteral(kind="hex", value="#1f6bb5")
    style.outline = ColorLiteral(kind="hex", value="#ff6f91")
    style.text_decoration_color = ColorLiteral(kind="hex", value="#f9d648")

    # Border
    style.border = Border(width=2.0, style="solid", color="#1f6bb5")
    style.border_radius = BorderRadius(
        top_left=Length(6.0, "px"),
        top_right=Length(6.0, "px"),
        bottom_right=Length(6.0, "px"),
        bottom_left=Length(6.0, "px"),
    )

    # Spacing
    style.padding = Insets(
        top=Length(8.0, "px"),
        right=Length(16.0, "px"),
        bottom=Length(8.0, "px"),
        left=Length(16.0, "px"),
    )
    style.margin = Insets(
        top=Length(4.0, "px"),
        right=Length(8.0, "px"),
        bottom=Length(4.0, "px"),
        left=Length(8.0, "px"),
    )

    # Typography
    style.font = "base"
    style.font_size = Length(15.0, "px")
    style.weight = 500
    style.line_height = 1.4
    style.letter_spacing = Length(0.5, "px")
    style.word_spacing = Length(1.0, "px")
    style.text_decoration = "underline"
    style.text_decoration_style = "dotted"
    style.text_transform = "uppercase"
    style.text_align = "center"
    style.vertical_align = "middle"

    # Text shadow
    style.text_shadow = TextShadow(
        offset_x=Length(1.0, "px"),
        offset_y=Length(1.0, "px"),
        blur_radius=Length(2.0, "px"),
        color=ColorLiteral(kind="rgba", value=(0, 0, 0, 0.5)),
    )

    # Box shadow
    style.box_shadow = [
        BoxShadow(
            offset_x=Length(0.0, "px"),
            offset_y=Length(4.0, "px"),
            blur_radius=Length(12.0, "px"),
            spread_radius=Length(0.0, "px"),
            color=ColorLiteral(kind="rgba", value=(0, 0, 0, 0.55)),
            inset=False,
        ),
    ]

    # Layout
    style.display = "flex"
    style.position = "relative"
    style.top = Length(0.0, "px")
    style.right = Length(0.0, "px")
    style.bottom = Length(0.0, "px")
    style.left = Length(0.0, "px")
    style.width = Length(320.0, "px")
    style.height = Length(240.0, "px")
    style.min_width = Length(160.0, "px")
    style.min_height = Length(120.0, "px")
    style.max_width = Length(640.0, "px")
    style.max_height = Length(480.0, "px")

    # Flexbox
    style.flex_direction = "row"
    style.flex_wrap = "nowrap"
    style.justify_content = "space-between"
    style.align_items = "center"
    style.align_content = "stretch"
    style.flex_grow = 1.0
    style.flex_shrink = 0.0
    style.flex_basis = Length(200.0, "px")
    style.align_self = "auto"

    # Grid
    style.grid_template_columns = "1fr 2fr 1fr"
    style.grid_template_rows = "auto 1fr auto"
    style.grid_gap = Length(16.0, "px")
    style.grid_column_gap = Length(16.0, "px")
    style.grid_row_gap = Length(8.0, "px")

    # Effects
    style.opacity = 0.98
    style.filter = "brightness(1.1)"
    style.transform = "scale(1.01)"
    style.transform_origin = "center center"

    # Background image/gradient
    style.background_image = Gradient(
        type="linear",
        colors=[
            (ColorLiteral(kind="hex", value="#3ea6ff"), 0.0),
            (ColorLiteral(kind="hex", value="#ff6f91"), 1.0),
        ],
        angle=90.0,
    )
    style.background_position = "center"
    style.background_size = "cover"
    style.background_repeat = "no-repeat"

    # Transitions
    style.transitions = [
        Transition(property="color", duration=0.3, delay=0.0, timing_function="ease"),
        Transition(property="background", duration=0.2, delay=0.0, timing_function="linear"),
    ]

    # Animations
    style.animations = [
        Animation(
            name="fade-in",
            duration=0.5,
            delay=0.0,
            timing_function="ease-out",
            iteration_count=1,
            direction="normal",
            fill_mode="forwards",
        ),
    ]

    # Keyframes
    style.keyframes = {
        "fade-in": Keyframes(
            name="fade-in",
            keyframes=[
                Keyframe(offset=0.0, properties={"opacity": "0", "transform": "translateY(-10px)"}),
                Keyframe(offset=1.0, properties={"opacity": "1", "transform": "translateY(0)"}),
            ],
        ),
    }

    # Custom properties and extras
    style.component_extras = {"telemetry": ["enabled"], "debug": ["verbose"]}
    style.raw_meta = {"source": "test", "version": 1}
    style.custom_properties = {"--panel-gap": "8px", "--card-border": "3px solid"}

    return style


def _serialize_backend_payload(payload: BackendStylePayload) -> dict[str, Any]:
    """Serialize BackendStylePayload to dict for display.

    Args:
        payload: The backend style payload to serialize.

    Returns:
        Dictionary representation of the payload.
    """
    return {
        "backend": str(payload.backend.value),
        "style": _serialize_for_display(payload.style),
        "renderer_metadata": payload.renderer_metadata,
        "layout_style": _serialize_for_display(payload.layout_style) if payload.layout_style else None,
        "extras": payload.extras,
    }


def _get_full_backend_styles(style: ResolvedStyle) -> tuple[BackendStylePayload, BackendStylePayload]:
    """Get full backend-conditioned styles for CLI and GUI.

    Args:
        style: The ResolvedStyle to convert.

    Returns:
        Tuple of (cli_payload, gui_payload).
    """
    from ornata.api.exports.definitions import CacheKey

    runtime = StylingRuntime()

    # CLI backend payload
    cli_context = StylingContext(
        component_name="TestComponent",
        state={},
        backend=BackendTarget.CLI,
        caps=_get_cli_caps(),
    )
    # Create cache key same way as StylingRuntime
    cli_caps_sig = hash(("C256", 96, (8, 16)))
    cli_key = CacheKey(
        component="TestComponent",
        states=frozenset(),
        overrides=tuple(),
        style_version=runtime._engine.theme_version,
        theme_version=runtime._theme_manager.version,
        caps_signature=cli_caps_sig,
    )
    runtime._cache[cli_key] = style
    cli_payload = runtime.resolve_backend_style(cli_context)

    # GUI backend payload
    gui_context = StylingContext(
        component_name="TestComponent",
        state={},
        backend=BackendTarget.GUI,
        caps=_get_gui_caps(),
    )
    gui_caps_sig = hash(("TRUECOLOR", 96, (8, 16)))
    gui_key = CacheKey(
        component="TestComponent",
        states=frozenset(),
        overrides=tuple(),
        style_version=runtime._engine.theme_version,
        theme_version=runtime._theme_manager.version,
        caps_signature=gui_caps_sig,
    )
    runtime._cache[gui_key] = style
    gui_payload = runtime.resolve_backend_style(gui_context)

    return cli_payload, gui_payload


def _serialize_for_display(obj: Any) -> Any:
    """Recursively serialize objects for JSON display.

    Args:
        obj: Object to serialize.

    Returns:
        JSON-serializable representation.
    """
    if hasattr(obj, "__dataclass_fields__"):
        return {
            field: _serialize_for_display(getattr(obj, field))
            for field in obj.__dataclass_fields__
            if getattr(obj, field) is not None
        }
    if isinstance(obj, (list, tuple)):
        return [_serialize_for_display(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _serialize_for_display(v) for k, v in obj.items()}
    return obj


def _write_output_files(style: ResolvedStyle, output_dir: Path) -> None:
    """Write mapper outputs to files for inspection.

    Args:
        style: The ResolvedStyle to map and output.
        output_dir: Directory to write output files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # CLI Mapping (old mapper)
    cli_mapper = CLIMapper(style)
    cli_mapper_output = cli_mapper.map()

    # GUI Mapping (old mapper)
    gui_mapper = GUIMapper(style)
    gui_mapper_output = gui_mapper.map_to_gui(
        cell_metrics=_cell_metrics,
        font_metrics=_font_metrics,
    )

    # Full backend-conditioned payloads
    cli_payload, gui_payload = _get_full_backend_styles(style)

    # Write old mapper outputs for comparison
    cli_mapper_path = output_dir / "cli_mapper_output.json"
    cli_mapper_path.write_text(json.dumps(cli_mapper_output, indent=2, default=str))

    gui_mapper_path = output_dir / "gui_mapper_output.json"
    gui_mapper_path.write_text(json.dumps(gui_mapper_output, indent=2, default=str))

    # Write full backend payloads
    cli_full_path = output_dir / "cli_backend_full.json"
    cli_full_path.write_text(json.dumps(_serialize_backend_payload(cli_payload), indent=2, default=str))

    gui_full_path = output_dir / "gui_backend_full.json"
    gui_full_path.write_text(json.dumps(_serialize_backend_payload(gui_payload), indent=2, default=str))

    # Write raw ResolvedStyle
    raw_path = output_dir / "resolved_style_raw.json"
    serialized = _serialize_for_display(style)
    raw_path.write_text(json.dumps(serialized, indent=2, default=str))

    # Write comparison report
    report_path = output_dir / "backend_comparison_report.txt"
    report_lines = [
        "=" * 70,
        "BACKEND STYLE COMPARISON - EVERY FIELD SHOWN",
        "=" * 70,
        "",
        ">>> CLI BACKEND (FULL PAYLOAD):",
        "-" * 70,
        f"Backend: {cli_payload.backend.value}",
        f"Total fields in style: {len([f for f in cli_payload.style.__dataclass_fields__ if getattr(cli_payload.style, f) is not None])}",
        "",
        "STYLE FIELDS:",
        json.dumps(_serialize_for_display(cli_payload.style), indent=2, default=str),
        "",
        "RENDERER METADATA:",
        json.dumps(cli_payload.renderer_metadata, indent=2, default=str),
        "",
        "LAYOUT STYLE:",
        json.dumps(_serialize_for_display(cli_payload.layout_style), indent=2, default=str) if cli_payload.layout_style else "None",
        "",
        "",
        ">>> GUI BACKEND (FULL PAYLOAD):",
        "-" * 70,
        f"Backend: {gui_payload.backend.value}",
        f"Total fields in style: {len([f for f in gui_payload.style.__dataclass_fields__ if getattr(gui_payload.style, f) is not None])}",
        "",
        "STYLE FIELDS:",
        json.dumps(_serialize_for_display(gui_payload.style), indent=2, default=str),
        "",
        "RENDERER METADATA:",
        json.dumps(gui_payload.renderer_metadata, indent=2, default=str),
        "",
        "LAYOUT STYLE:",
        json.dumps(_serialize_for_display(gui_payload.layout_style), indent=2, default=str) if gui_payload.layout_style else "None",
        "",
        "",
        "=" * 70,
        "FIELD COUNT COMPARISON",
        "=" * 70,
        f"CLI style fields: {len([f for f in cli_payload.style.__dataclass_fields__ if getattr(cli_payload.style, f) is not None])}",
        f"GUI style fields: {len([f for f in gui_payload.style.__dataclass_fields__ if getattr(gui_payload.style, f) is not None])}",
        "",
        f"Files written to: {output_dir.absolute()}",
        f"  - {cli_full_path.name} (CLI full backend payload)",
        f"  - {gui_full_path.name} (GUI full backend payload)",
        f"  - {raw_path.name} (Raw ResolvedStyle)",
        f"  - {cli_mapper_path.name} (Old CLI mapper - limited)",
        f"  - {gui_mapper_path.name} (Old GUI mapper - limited)",
        f"  - {report_path.name} (This report)",
    ]
    report_path.write_text("\n".join(report_lines))

    # Also print summary to console
    print("\n".join(report_lines[:20]))  # Print first 20 lines
    print(f"\n... see full output in {report_path}")


def test_resolved_style_cli_mapping() -> None:
    """Build complete ResolvedStyle and output CLI backend payload."""
    style = build_complete_resolved_style()
    output_dir = Path("tests/styling/output")
    _write_output_files(style, output_dir)

    cli_full_path = output_dir / "cli_backend_full.json"
    assert cli_full_path.exists()

    cli_payload = json.loads(cli_full_path.read_text())
    assert "style" in cli_payload
    assert cli_payload["backend"] == "cli"


def test_resolved_style_gui_mapping() -> None:
    """Build complete ResolvedStyle and output GUI backend payload."""
    style = build_complete_resolved_style()
    output_dir = Path("tests/styling/output")
    _write_output_files(style, output_dir)

    gui_full_path = output_dir / "gui_backend_full.json"
    assert gui_full_path.exists()

    gui_payload = json.loads(gui_full_path.read_text())
    assert "style" in gui_payload
    assert gui_payload["backend"] == "gui"


def test_resolved_style_both_mappers() -> None:
    """Build complete ResolvedStyle and output both CLI and GUI full backend payloads."""
    style = build_complete_resolved_style()
    output_dir = Path("tests/styling/output")
    _write_output_files(style, output_dir)

    # Verify all output files exist
    assert (output_dir / "cli_backend_full.json").exists()
    assert (output_dir / "gui_backend_full.json").exists()
    assert (output_dir / "resolved_style_raw.json").exists()
    assert (output_dir / "backend_comparison_report.txt").exists()

    # Load and verify full backend payloads
    cli_payload = json.loads((output_dir / "cli_backend_full.json").read_text())
    gui_payload = json.loads((output_dir / "gui_backend_full.json").read_text())

    # Both should have full style data
    assert cli_payload["backend"] == "cli"
    assert gui_payload["backend"] == "gui"
    assert "style" in cli_payload
    assert "style" in gui_payload
    assert "renderer_metadata" in cli_payload
    assert "renderer_metadata" in gui_payload
