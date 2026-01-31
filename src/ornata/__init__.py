"""
Ornata Package exports.

# Quick links

- [Overview](#overview)
- [Licensing & Copyright](#licensing-and-copyright)
- [See Also](#see-also)

---

# Overview

The `ornata` package provides a **high-performance UI framework** for building modern applications.

---

# See Also

- [API](ornata.api)
- [Application](ornata.application)
- [Components](ornata.components)
- [Core](ornata.core)
- [Effects](ornata.effects)
- [Events](ornata.events)
- [GPU](ornata.gpu)
- [Interop](ornata.interop)
- [Kernel](ornata.kernel)
- [Layout](ornata.layout)
- [Optimization](ornata.optimization)
- [Plugins](ornata.plugins)
- [Rendering](ornata.rendering)
- [Styling](ornata.styling)
- [Utils](ornata.utils)
- [VDOM](ornata.vdom)

---

# Licensing & Copyright
**Copyright** © 2024 Ornata Contributors
**License**: MIT

"""

from __future__ import annotations

from . import __main__, _lazy, api, application, cli, components, core, effects, events, gpu, interop, kernel, layout, optimization, plugins, rendering, styling, utils, vdom
from ._lazy import __getattr__

__all__ = [
    "__getattr__",
    "__main__",
    "_lazy",
    "api",
    "application",
    "cli",
    "components",
    "core",
    "effects",
    "events",
    "gpu",
    "interop",
    "kernel",
    "layout",
    "optimization",
    "plugins",
    "rendering",
    "styling",
    "utils",
    "vdom",
]