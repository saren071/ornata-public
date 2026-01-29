"""Simple GPU resource handles and manager for the public API."""

from __future__ import annotations

import threading
import uuid
from typing import TYPE_CHECKING, Any

from ornata.api.exports.definitions import GPUBufferHandle, GPUTextureHandle

if TYPE_CHECKING:
    from ornata.api.exports.definitions import GPUResourceHandle


def _new_resource_id() -> str:
    """Generate a short unique GPU resource identifier."""

    return f"gpu_res_{uuid.uuid4().hex}"


class GPUResourceManager:
    """Registry for GPU resources shared by the public API."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._resources: dict[str, GPUResourceHandle] = {}

    def register(self, handle: GPUResourceHandle) -> GPUResourceHandle:
        """Register a GPU resource handle."""

        with self._lock:
            self._resources[handle.resource_id] = handle
        return handle

    def dispose_resource(self, resource_id: str) -> None:
        """Drop a resource handle (if known)."""

        with self._lock:
            self._resources.pop(resource_id, None)

    def get_handle(self, resource_id: str) -> GPUResourceHandle | None:
        """Get a previously registered handle."""

        with self._lock:
            return self._resources.get(resource_id)


_RESOURCE_MANAGER = GPUResourceManager()


def get_gpu_resource_manager() -> GPUResourceManager:
    """Return the shared GPU resource manager."""

    return _RESOURCE_MANAGER


def create_gpu_buffer(size_bytes: int, *, usage: str | None = None, metadata: dict[str, Any] | None = None) -> GPUBufferHandle:
    """Generate a registered GPU buffer handle."""

    buffer_handle = GPUBufferHandle(
        resource_id=_new_resource_id(),
        size_bytes=size_bytes,
        usage=usage,
        metadata=(metadata or {}),
    )
    return _RESOURCE_MANAGER.register(buffer_handle)


def create_gpu_texture(
    width: int,
    height: int,
    format_name: str,
    pixel_data: bytes | None = None,
    *,
    mip_levels: int = 1,
    metadata: dict[str, Any] | None = None,
) -> GPUTextureHandle:
    """Generate a registered GPU texture handle."""

    texture_metadata = dict(metadata or {})
    texture_metadata.setdefault("format", format_name)
    if pixel_data is not None:
        texture_metadata.setdefault("size_bytes", len(pixel_data))
    texture_handle = GPUTextureHandle(
        resource_id=_new_resource_id(),
        width=width,
        height=height,
        mip_levels=mip_levels,
        metadata=texture_metadata,
    )
    return _RESOURCE_MANAGER.register(texture_handle)
