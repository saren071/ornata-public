""" VDOM Dataclasses for Ornata """

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ornata.api.exports.vdom import TreePatcher, TreeReconciler, _clear_subtree_dirty, _clone_props_dict, _recompute_node_hash
from ornata.definitions.enums import BackendTarget, PatchType
from ornata.definitions.errors import ComponentNotFoundError, InvalidVDOMOperationError

if TYPE_CHECKING:
    from collections.abc import Callable

    from ornata.definitions.dataclasses.components import Component


@dataclass(slots=True)
class Patch:
    """Represents a single diffing patch."""
    patch_type: PatchType
    key: str | None = None
    data: Any = None

    @classmethod
    def add_node(cls, node: VDOMNode) -> Patch:
        return cls(PatchType.ADD_NODE, key=node.key, data=node)

    @classmethod
    def remove_node(cls, key: str) -> Patch:
        return cls(PatchType.REMOVE_NODE, key=key)

    @classmethod
    def update_props(cls, key: str, props: dict[str, Any]) -> Patch:
        return cls(PatchType.UPDATE_PROPS, key=key, data=props)

    @classmethod
    def move_node(cls, key: str, new_position: int) -> Patch:
        return cls(PatchType.MOVE_NODE, key=key, data=new_position)

    @classmethod
    def replace_root(cls, new_root: VDOMNode) -> Patch:
        return cls(PatchType.REPLACE_ROOT, data=new_root)


@dataclass(slots=True)
class VDOMNode:
    """VDOM tree node representing a component snapshot."""
    component_name: str
    props: dict[str, Any] = field(default_factory=dict)
    children: list[VDOMNode] = field(default_factory=list)
    key: str | None = None
    parent_key: str | None = None
    child_index: int = 0
    normalized_props: tuple[tuple[str, Any], ...] = field(default_factory=tuple, init=False, repr=False)
    props_hash: int = field(default=0, init=False, repr=False)
    child_hash: int = field(default=0, init=False, repr=False)
    subtree_hash: int = field(default=0, init=False, repr=False)
    dirty: bool = field(default=False, init=False, repr=False)
    props_dirty: bool = field(default=True, init=False, repr=False)

    def clone(self, *, parent_key: str | None = None, index: int | None = None) -> VDOMNode:
        clone_index = self.child_index if index is None else index
        cloned = VDOMNode(
            component_name=self.component_name,
            props=_clone_props_dict(self.props),
            children=[],
            key=self.key,
            parent_key=parent_key,
            child_index=clone_index,
        )
        for idx, child in enumerate(self.children):
            cloned_child = child.clone(parent_key=cloned.key, index=idx)
            cloned.children.append(cloned_child)
        cloned.normalized_props = tuple(self.normalized_props)
        cloned.props_hash = self.props_hash
        cloned.child_hash = self.child_hash
        cloned.subtree_hash = self.subtree_hash
        cloned.props_dirty = False
        return cloned


@dataclass(slots=True)
class VDOMTree:
    """Virtual DOM tree for efficient component management."""
    root: VDOMNode | None = None
    backend_target: BackendTarget = BackendTarget.CLI
    _component_refs: dict[str, Any] = field(default_factory=dict)
    key_map: dict[str, VDOMNode] = field(default_factory=dict)
    _lock: threading.RLock = field(default_factory=threading.RLock)
    _reconciler: TreeReconciler = field(default_factory=TreeReconciler)
    _patcher: TreePatcher = field(default_factory=TreePatcher)
    _node_count: int = 0
    _dirty_keys: set[str] = field(default_factory=set, init=False)
    _structural_keys: set[str] = field(default_factory=set, init=False)
    _host_factory: Callable[[VDOMNode], Any] | None = field(default=None, init=False, repr=False)
    _host_apply_props: Callable[[Any, dict[str, Any]], None] | None = field(default=None, init=False, repr=False)
    _host_move: Callable[[Any, int], None] | None = field(default=None, init=False, repr=False)

    def update_component(self, key: str, new_component: Component) -> list[Patch]:
        with self._lock:
            if key not in self.key_map:
                raise ComponentNotFoundError(f"Component with key '{key}' not found")
            old_node = self.key_map[key]
            new_node = self._component_to_node(
                new_component,
                parent_key=old_node.parent_key,
                position=old_node.child_index,
            )
            self._initialize_hashes(new_node)
            patches = self._reconciler.reconcile(old_node, new_node, None)
            self._patcher.apply_patches(self, patches)
            self._component_refs[key] = new_component
            return patches

    def add_component(self, component: Component, key: str | None = None) -> str:
        with self._lock:
            node = self._component_to_node(component, parent_key=None, position=0)
            if key is None:
                key = node.key or self._generate_key()
            elif key in self.key_map:
                raise InvalidVDOMOperationError(f"Component with key '{key}' already exists")

            if key in self.key_map:
                raise InvalidVDOMOperationError(f"Component with key '{key}' already exists")
            node.key = key
            mark_dirty = self.root is not None
            self.attach_node(node, parent_key=None, position=0, mark_dirty=mark_dirty)
            self._component_refs[key] = component
            return key

    def remove_component(self, key: str) -> None:
        with self._lock:
            if key not in self.key_map:
                return
            self.detach_subtree(key)
            self._component_refs.pop(key, None)

    def get_component(self, key: str) -> Any | None:
        with self._lock:
            return self._component_refs.get(key)

    @property
    def node_count(self) -> int:
        return self._node_count

    def consume_dirty_state(self) -> tuple[set[str], set[str]] | None:
        with self._lock:
            if not self._dirty_keys and not self._structural_keys:
                return None
            dirty = set(self._dirty_keys)
            structural = set(self._structural_keys)
            self._dirty_keys.clear()
            self._structural_keys.clear()
            self._clear_dirty_nodes(dirty | structural)
            return dirty, structural

    def reset_dirty_tracking(self) -> None:
        with self._lock:
            if not self._dirty_keys and not self._structural_keys:
                return
            dirty = set(self._dirty_keys)
            structural = set(self._structural_keys)
            self._dirty_keys.clear()
            self._structural_keys.clear()
            self._clear_dirty_nodes(dirty | structural)

    def _initialize_hashes(self, node: VDOMNode) -> None:
        for child in node.children:
            self._initialize_hashes(child)
        _recompute_node_hash(node)
        _clear_subtree_dirty(node)

    def _bubble_hashes(self, node: VDOMNode | None) -> None:
        current = node
        while current is not None:
            _recompute_node_hash(current)
            parent_key = current.parent_key
            current = self.key_map.get(parent_key) if parent_key is not None else None

    def _mark_node_dirty(self, node: VDOMNode | None) -> None:
        self._mark_dirty_chain(node, structural=False)

    def _mark_hierarchy_dirty(self, node: VDOMNode | None) -> None:
        self._mark_dirty_chain(node, structural=True)

    def _mark_dirty_chain(self, node: VDOMNode | None, structural: bool) -> None:
        current = node
        while current is not None:
            key = getattr(current, "key", None)
            if key:
                self._dirty_keys.add(key)
                if structural:
                    self._structural_keys.add(key)
            current.dirty = True
            parent_key = current.parent_key
            current = self.key_map.get(parent_key) if parent_key is not None else None

    def _clear_dirty_nodes(self, keys: set[str]) -> None:
        for key in keys:
            node = self.key_map.get(key)
            if node is not None:
                node.dirty = False

    def attach_node(self, node: VDOMNode, parent_key: str | None, position: int | None, *, mark_dirty: bool = True) -> VDOMNode:
        with self._lock:
            if node.key is None:
                node.key = self._generate_key()
            node.parent_key = parent_key
            node.child_index = 0 if position is None else position
            if node.key in self.key_map:
                raise InvalidVDOMOperationError(f"Node with key '{node.key}' already exists")
            parent = None
            if parent_key is None:
                self.root = node
            else:
                parent = self.key_map.get(parent_key)
                if parent is None:
                    raise InvalidVDOMOperationError(f"Parent '{parent_key}' not found for attach")
                insert_at = max(0, min(node.child_index, len(parent.children)))
                parent.children.insert(insert_at, node)
                self._reindex_children(parent)
            self._register_subtree(node)
            self._initialize_hashes(node)
            bubble_target = node if parent_key is None else parent
            self._bubble_hashes(bubble_target)
            if mark_dirty:
                if parent_key is None:
                    self._mark_node_dirty(node)
                else:
                    if parent is not None:
                        self._mark_hierarchy_dirty(parent)
            return node

    def detach_subtree(self, key: str) -> None:
        with self._lock:
            node = self.key_map.get(key)
            if node is None:
                return
            parent_key = node.parent_key
            if parent_key is not None:
                parent = self.key_map.get(parent_key)
                if parent is not None:
                    self._mark_node_dirty(parent)
            if parent_key is None:
                self.root = None
            else:
                parent = self.key_map.get(parent_key)
                if parent is not None:
                    parent.children = [child for child in parent.children if child.key != key]
                    self._reindex_children(parent)
            self._unregister_subtree(node)
            if parent_key is not None:
                parent = self.key_map.get(parent_key)
                self._bubble_hashes(parent)
                self._mark_hierarchy_dirty(parent)

    def move_node(self, key: str, new_index: int) -> None:
        with self._lock:
            node = self.key_map.get(key)
            if node is None or node.parent_key is None:
                return
            parent = self.key_map.get(node.parent_key)
            if parent is None:
                return
            children = parent.children
            try:
                current_index = next(idx for idx, child in enumerate(children) if child.key == key)
            except StopIteration:
                return
            child = children.pop(current_index)
            insert_at = max(0, min(new_index, len(children)))
            children.insert(insert_at, child)
            self._reindex_children(parent)
            self._bubble_hashes(parent)
            self._mark_node_dirty(child)
            self._mark_hierarchy_dirty(parent)

    def update_node_props(self, key: str, props: dict[str, Any]) -> None:
        with self._lock:
            node = self.key_map.get(key)
            if node is None:
                raise ComponentNotFoundError(f"Component with key '{key}' not found")
            node.props.update(props)
            node.props_dirty = True
            self._bubble_hashes(node)
            self._mark_node_dirty(node)

    def _component_to_node(
        self,
        component: Component,
        *,
        parent_key: str | None = None,
        position: int = 0,
    ) -> VDOMNode:
        key = self._ensure_component_key(component)
        if hasattr(component, "__dict__"):
            props: dict[str, Any] = _clone_props_dict(component.__dict__)
        else:
            props = {}

        props.pop("children", None)
        props.pop("__weakref__", None)
        children_nodes: list[VDOMNode] = []
        children_seq: list[Component | str] = list(getattr(component, "children", None) or [])
        for idx, child in enumerate(children_seq):
            children_nodes.append(self._convert_child(child, key, idx))
        node = VDOMNode(
            component_name=getattr(component, "component_name", type(component).__name__),
            props=props,
            children=children_nodes,
            key=key,
            parent_key=parent_key,
            child_index=position,
        )
        node.props_dirty = True
        return node

    def _convert_child(self, child: Any, parent_key: str | None, position: int) -> VDOMNode:
        original_name = getattr(child, "component_name", None)
        renderable_child: Any | None = None
        if hasattr(child, "to_renderable"):
            renderable_child = child.to_renderable()
            node = self._normalize_child_node(renderable_child, parent_key, position)
        else:
            node = self._normalize_child_node(child, parent_key, position)

        if original_name and renderable_child is not None:
            try:
                from ornata.api.exports.definitions import Component as ComponentBase
            except Exception:
                ComponentBase = None
            if ComponentBase is not None and isinstance(renderable_child, ComponentBase):
                node.component_name = original_name

        return node

    def _normalize_child_node(self, child: Any, parent_key: str | None, position: int) -> VDOMNode:
        try:
            from ornata.api.exports.definitions import Component as ComponentBase
        except Exception:
            ComponentBase = None
        if ComponentBase is not None and isinstance(child, ComponentBase):
            return self._component_to_node(child, parent_key=parent_key, position=position)
        return self._create_text_node(str(child), parent_key=parent_key, position=position)

    def _create_text_node(self, value: str, parent_key: str | None, position: int) -> VDOMNode:
        text_key = f"text-{self._generate_key()}"
        return VDOMNode(
            component_name="text",
            props={"content": value},
            children=[],
            key=text_key,
            parent_key=parent_key,
            child_index=position,
        )

    def _ensure_component_key(self, component: Component) -> str:
        key_value = getattr(component, "key", None)
        if isinstance(key_value, str) and key_value:
            return key_value
        if key_value:
            key_str = str(key_value)
            component.key = key_str
            return key_str
        candidate = getattr(component, "component_id", None)
        if isinstance(candidate, str) and candidate:
            key_value = candidate
        else:
            candidate_name = getattr(component, "name", None)
            if isinstance(candidate_name, str) and candidate_name:
                key_value = f"{candidate_name}-{self._generate_key()}"
            else:
                key_value = self._generate_key()
        component.key = key_value
        return key_value

    def _register_subtree(self, node: VDOMNode) -> None:
        if node.key is None:
            node.key = self._generate_key()
        self.key_map[node.key] = node
        self._node_count += 1
        for idx, child in enumerate(node.children):
            child.parent_key = node.key
            child.child_index = idx
            self._register_subtree(child)

    def _unregister_subtree(self, node: VDOMNode) -> None:
        if node.key is not None:
            self.key_map.pop(node.key, None)
        if self._node_count > 0:
            self._node_count -= 1
        for child in node.children:
            self._unregister_subtree(child)

    def _reindex_children(self, parent: VDOMNode) -> None:
        for idx, child in enumerate(parent.children):
            child.child_index = idx
            child.parent_key = parent.key

    def _generate_key(self) -> str:
        while True:
            key = str(uuid.uuid4())[:8]
            if key not in self.key_map:
                return key


@dataclass(slots=True)
class PatchPoolConfig:
    """Configuration for patch object pooling behavior."""
    max_pool_size: int = 2000
    max_idle_time: float = 300.0
    cleanup_interval: float = 60.0
    enable_weak_refs: bool = False


@dataclass(slots=True)
class PatchPoolStats:
    """Statistics for patch pool usage and performance."""
    created: int = 0
    reused: int = 0
    returned: int = 0
    evicted: int = 0
    garbage_collected: int = 0
    pool_size: int = 0
    hit_rate: float = 0.0

__all__ = [
    "Patch",
    "PatchPoolConfig",
    "PatchPoolStats",
    "VDOMNode",
    "VDOMTree",
]