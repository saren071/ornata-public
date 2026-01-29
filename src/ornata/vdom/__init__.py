"""Exports for ornata.vdom.

# Quick links (to sections in this file)

- [Overview](#overview)
- [Core](#core)
- [Diffing](#diffing)
- [Memory](#memory)

# Overview

The `ornata.vdom` module provides the core VDOM (Virtual DOM) functionality for Ornata.

## Core

The `ornata.vdom.core` module provides the core VDOM (Virtual DOM) functionality for Ornata.

## Diffing

The `ornata.vdom.diffing` module provides the diffing functionality for Ornata.

## Memory

The `ornata.vdom.memory` module provides the memory management functionality for Ornata.

---

## See Also

- [ornata.vdom.core.binding_integration](ornata.vdom.core.binding_integration)
- [ornata.vdom.core.bindings](ornata.vdom.core.bindings)
- [ornata.vdom.core.host_objects](ornata.vdom.core.host_objects)
- [ornata.vdom.core.interfaces](ornata.vdom.core.interfaces)
- [ornata.vdom.core.keys](ornata.vdom.core.keys)
- [ornata.vdom.core.refs](ornata.vdom.core.refs)
- [ornata.vdom.core.tree](ornata.vdom.core.tree)
- [ornata.vdom.diffing.algorithms](ornata.vdom.diffing.algorithms)
- [ornata.vdom.diffing.cache](ornata.vdom.diffing.cache)
- [ornata.vdom.diffing.engine](ornata.vdom.diffing.engine)
- [ornata.vdom.diffing.incremental](ornata.vdom.diffing.incremental)
- [ornata.vdom.diffing.interfaces](ornata.vdom.diffing.interfaces)
- [ornata.vdom.diffing.lifecycle](ornata.vdom.diffing.lifecycle)
- [ornata.vdom.diffing.object_pool](ornata.vdom.diffing.object_pool)
- [ornata.vdom.diffing.optimization](ornata.vdom.diffing.optimization)
- [ornata.vdom.diffing.patcher](ornata.vdom.diffing.patcher)
- [ornata.vdom.diffing.reconciler](ornata.vdom.diffing.reconciler)
- [ornata.vdom.diffing.scheduler](ornata.vdom.diffing.scheduler)
- [ornata.vdom.memory.memory](ornata.vdom.memory.memory)

"""

from __future__ import annotations

from . import core, diffing, memory

__all__ = [
    "core",
    "diffing",
    "memory",
]
