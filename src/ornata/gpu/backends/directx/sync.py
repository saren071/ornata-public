# ===========================
# ornata/gpu/backends/directx/sync.py
# ===========================
"""DirectX synchronization primitives module.

Implements GPU-CPU synchronization using D3D11 query objects. This is suitable
for simple "signal + wait" semantics in the immediate context.

- create_fence() returns an ID3D11Query with D3D11_QUERY_EVENT
- signal_fence(f) calls End(f) on the immediate context
- wait_for_fence(f, timeout_ms) polls GetData until signaled or timeout
"""

from __future__ import annotations

import ctypes
import time
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.interop import ID3D11Device, ID3D11Query

logger = get_logger(__name__)


class DirectXSync:
    """Manages D3D11 query-based synchronization."""

    def __init__(self, device: ID3D11Device | None) -> None:
        from ornata.api.exports.interop import ID3D11DeviceContext
        if device is None:
            raise ValueError("DirectXSync requires a valid ID3D11Device")
        self._device = device
        # Try to obtain the immediate context if available via the device
        ctx_getter = getattr(self._device, "GetImmediateContext", None)
        ctx: ID3D11DeviceContext | None = None
        if callable(ctx_getter):
            ctx = ID3D11DeviceContext()
            try:
                # Some wrappers expose GetImmediateContext(ctx_out) → None
                # If the attribute exists, invoke it; otherwise leave ctx as None.
                ctx_getter(ctx)
            except Exception:
                ctx = None
        # COM contexts expose methods like End/GetData that are not visible to type checkers.
        # We treat the context as dynamic here to avoid over-constraining the interface.
        self._context: Any | None = ctx
        self._initialized = True

    def create_fence(self) -> ID3D11Query:
        """Create a D3D11_QUERY_EVENT query object to act as a fence."""
        if not self._initialized:
            raise RuntimeError("DirectXSync not initialized")
        from ornata.api.exports.interop import D3D11_QUERY_DESC, D3D11_QUERY_EVENT, ID3D11Query

        query_ptr = ID3D11Query()
        desc = D3D11_QUERY_DESC()
        desc.Query = D3D11_QUERY_EVENT
        desc.MiscFlags = 0

        hr = self._device.CreateQuery(desc, query_ptr)
        if int(hr) != 0:
            raise RuntimeError(f"CreateQuery failed: hr={hr}")
        return query_ptr

    def signal_fence(self, fence: ID3D11Query) -> None:
        """Signal a fence by ending the event query on the immediate context."""
        if self._context is None:
            raise RuntimeError("Immediate context unavailable for signaling fence")
        self._context.End(fence)

    def wait_for_fence(self, fence: ID3D11Query, timeout_ms: int = 5000) -> None:
        """Block until the fence is signaled or timeout occurs.

        Args:
            fence: Fence query returned by `create_fence`.
            timeout_ms: Maximum time to wait before raising `TimeoutError`.
        """
        if self._context is None:
            raise RuntimeError("Immediate context unavailable for waiting on fence")

        start = time.perf_counter()
        data = ctypes.c_uint(0)
        sizeof_data = ctypes.sizeof(data)

        while True:
            # GetData returns S_OK when data is ready; `data` becomes TRUE if event occurred
            hr = self._context.GetData(fence, ctypes.byref(data), sizeof_data, 0)
            if hr == 0 and data.value != 0:  # S_OK + TRUE
                return
            if (time.perf_counter() - start) * 1000.0 > float(timeout_ms):
                raise TimeoutError("Fence wait timed out")
            time.sleep(0.0005)  # be polite to the scheduler