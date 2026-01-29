"""Auto-generated exports for ornata.gpu.memory."""

from __future__ import annotations

from . import allocator, residency, staging, sync
from .allocator import Allocator
from .residency import Residency
from .staging import (
    Staging,
    _coerce_transfer_data,  # type: ignore [private]
)
from .sync import Sync

__all__ = [
    "Allocator",
    "_coerce_transfer_data",
    "Residency",
    "Staging",
    "allocator",
    "residency",
    "staging",
    "Sync",
    "sync",
]
