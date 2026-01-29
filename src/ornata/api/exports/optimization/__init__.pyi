"""Type stubs for the optimization subsystem exports."""

from __future__ import annotations

from ornata.optimization import cython as cython
from ornata.optimization.cython import compiler as compiler
from ornata.optimization.cython import extensions as extensions
from ornata.optimization.cython.compiler import check_cython_available as check_cython_available
from ornata.optimization.cython.compiler import compile_cython_extensions as compile_cython_extensions
from ornata.optimization.cython.compiler import get_extension_suffix as get_extension_suffix
from ornata.optimization.cython.extensions import _load_extension as _load_extension  #type: ignore
from ornata.optimization.cython.extensions import color_ops as color_ops
from ornata.optimization.cython.extensions import event_coalescing as event_coalescing
from ornata.optimization.cython.extensions import event_dispatch as event_dispatch
from ornata.optimization.cython.extensions import event_optimizer as event_optimizer
from ornata.optimization.cython.extensions import event_queue as event_queue
from ornata.optimization.cython.extensions import event_structs as event_structs
from ornata.optimization.cython.extensions import get_extension_status as get_extension_status
from ornata.optimization.cython.extensions import is_native_extension as is_native_extension  #type: ignore
from ornata.optimization.cython.extensions import log_extension_status as log_extension_status
from ornata.optimization.cython.extensions import style_ops as style_ops

__all__ = [
    "color_ops",
    "style_ops",
    "event_queue",
    "event_coalescing",
    "event_dispatch",
    "event_structs",
    "event_optimizer",
    "_load_extension",
    "check_cython_available",
    "compile_cython_extensions",
    "compiler",
    "cython",
    "extensions",
    "get_extension_status",
    "get_extension_suffix",
    "is_native_extension",
    "log_extension_status",
]