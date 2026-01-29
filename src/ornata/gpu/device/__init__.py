"""Auto-generated exports for ornata.gpu.device."""

from __future__ import annotations

from . import capabilities, device, geometry, limits, selection
from .capabilities import Capabilities
from .device import (
    DeviceManager,
    get_device_manager,
    render_with_gpu_acceleration,
)
from .geometry import (
    GeometryConverter,
    component_to_gpu_geometry,
    cpu_render,
    get_geometry_converter,
)
from .limits import Limits
from .selection import DeviceSelector

__all__ = [
    "Capabilities",
    "DeviceManager",
    "DeviceSelector",
    "GeometryConverter",
    "Limits",
    "capabilities",
    "component_to_gpu_geometry",
    "cpu_render",
    "device",
    "geometry",
    "get_device_manager",
    "get_geometry_converter",
    "limits",
    "render_with_gpu_acceleration",
    "selection",
]
