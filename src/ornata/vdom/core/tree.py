"""VDOM tree structures and management."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import VDOMNode

logger = get_logger(__name__)


def _normalize_prop_value(
    value: str | int | float | bool | dict[str, Any] | list[Any] | tuple[Any, ...] | set[Any] | None,
) -> Any:
    """Normalize property values into hash-friendly structures."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        # Keys are treated as strings for normalization purposes.
        return tuple((k, _normalize_prop_value(v)) for k, v in sorted(value.items()))
    if isinstance(value, (list, tuple)):
        return tuple(_normalize_prop_value(item) for item in value)
    if isinstance(value, set):
        return tuple(sorted(_normalize_prop_value(item) for item in value))
    return repr(value)


def _normalize_props_map(props: dict[str, Any] | None) -> tuple[tuple[str, Any], ...]:
    if not props:
        return ()
    return tuple((key, _normalize_prop_value(value)) for key, value in sorted(props.items()))


def _clone_prop_value(
    value: str | int | float | bool | dict[str, Any] | list[Any] | tuple[Any, ...] | set[Any] | None,
) -> Any:
    """Efficiently clone property payloads without relying on deepcopy for every node."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {key: _clone_prop_value(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_clone_prop_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_clone_prop_value(item) for item in value)
    if isinstance(value, set):
        return {_clone_prop_value(item) for item in value}
    return value


def _clone_props_dict(props: dict[str, Any]) -> dict[str, Any]:
    """Clone a props dictionary while preserving nested structures."""
    if not props:
        return {}
    mapping: dict[str, Any] = props
    return {key: _clone_prop_value(value) for key, value in mapping.items()}


def _recompute_node_hash(node: VDOMNode) -> None:
    """Recompute cached hash data for ``node`` using its current children."""
    normalized = node.normalized_props
    if node.props_dirty:
        normalized = _normalize_props_map(getattr(node, "props", None))
        node.normalized_props = normalized
        node.props_hash = hash(normalized)
        node.props_dirty = False
    child_hash = 0
    for child in node.children:
        child_hash ^= getattr(child, "subtree_hash", 0)
    node.child_hash = child_hash
    node.subtree_hash = hash((node.component_name, node.props_hash, child_hash))


def _clear_subtree_dirty(node: VDOMNode | None) -> None:
    if node is None:
        return
    node.dirty = False
    for child in node.children:
        _clear_subtree_dirty(child)


# Make internal helpers visible to static analysis to avoid unused-function diagnostics.
_ = (_clone_props_dict, _recompute_node_hash)
