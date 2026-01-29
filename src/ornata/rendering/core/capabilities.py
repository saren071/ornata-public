"""Renderer capability detection and specification.

Defines what features each renderer type supports, enabling conditional
feature usage based on renderer capabilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import BackendTarget, RendererCapabilities


logger = get_logger(__name__)


def get_cli_capabilities() -> RendererCapabilities:
    """Get capabilities for CLI Backend.
    
    Returns
    -------
    RendererCapabilities
        CLI Backend capabilities.
    """
    from ornata.api.exports.definitions import BackendTarget, RenderCapability, RendererCapabilities

    return RendererCapabilities(
        backend_type=BackendTarget.CLI,
        capabilities=(
            RenderCapability.COLOR
            | RenderCapability.STYLING
            | RenderCapability.UNICODE
            | RenderCapability.INTERACTIVE
        ),
        max_colors=256,
        supports_truecolor=True,
        frame_rate=30.0,
    )


def get_tty_capabilities() -> RendererCapabilities:
    """Get capabilities for TTY Backend.
    
    Returns
    -------
    RendererCapabilities
        TTY Backend capabilities.
    """
    from ornata.api.exports.definitions import BackendTarget, RenderCapability, RendererCapabilities

    return RendererCapabilities(
        backend_type=BackendTarget.TTY,
        capabilities=(
            RenderCapability.COLOR
            | RenderCapability.STYLING
            | RenderCapability.UNICODE
            | RenderCapability.INTERACTIVE
        ),
        max_colors=256,
        supports_truecolor=True,
        frame_rate=30.0,
    )


def get_gui_capabilities() -> RendererCapabilities:
    """Get capabilities for GUI Backend.
    
    Returns
    -------
    RendererCapabilities
        GUI Backend capabilities.
    """
    from ornata.api.exports.definitions import BackendTarget, RenderCapability, RendererCapabilities

    return RendererCapabilities(
        backend_type=BackendTarget.GUI,
        capabilities=(
            RenderCapability.COLOR
            | RenderCapability.ALPHA
            | RenderCapability.STYLING
            | RenderCapability.LAYERS
            | RenderCapability.ANIMATION
            | RenderCapability.IMAGES
            | RenderCapability.VECTORS
            | RenderCapability.HARDWARE_ACCEL
            | RenderCapability.INTERACTIVE
            | RenderCapability.UNICODE
            | RenderCapability.EMOJI
            | RenderCapability.CUSTOM_FONTS
        ),
        supports_truecolor=True,
        frame_rate=60.0,
    )


def get_capabilities(backend_type: BackendTarget) -> RendererCapabilities:
    """Get capabilities for any renderer type.
    
    Parameters
    ----------
    backend_type : BackendTarget
        The renderer type.
        
    Returns
    -------
    RendererCapabilities
        Capabilities for the specified renderer.
    """
    from ornata.api.exports.definitions import BackendTarget

    if backend_type == BackendTarget.CLI:
        return get_cli_capabilities()
    elif backend_type == BackendTarget.TTY:
        return get_tty_capabilities()
    elif backend_type == BackendTarget.GUI:
        return get_gui_capabilities()
