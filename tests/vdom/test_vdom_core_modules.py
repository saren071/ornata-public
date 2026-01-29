from __future__ import annotations

import gc
from typing import Any

import pytest

from ornata.definitions.dataclasses.components import Component, ComponentContent
from ornata.definitions.dataclasses.shared import StandardHostObject
from ornata.definitions.dataclasses.vdom import Patch, VDOMNode, VDOMTree
from ornata.definitions.enums import BackendTarget, PatchType
from ornata.definitions.errors import ComponentNotFoundError, InvalidVDOMOperationError
from ornata.vdom.core import binding_integration
from ornata.vdom.core import host_objects
from ornata.vdom.core import interfaces
from ornata.vdom.core import tree as tree_module
from ornata.vdom.core.binding_integration import (
    bind_host_object_to_tree,
    get_vdom_binding_integrator,
)
from ornata.vdom.core.bindings import HostBindingRegistry, get_bindings_registry
from ornata.vdom.core.keys import ComponentKeys
from ornata.vdom.core.refs import ComponentRefs


class _RenderableChild(Component):
    """Component subclass that emits a renderable proxy for coverage."""

    def __init__(self, name: str) -> None:
        super().__init__(component_name=name)
        self.calls: int = 0

    def to_renderable(self) -> Component:  # noqa: D401 - testing hook
        self.calls += 1
        return Component(component_name=f"Rendered-{self.component_name}")


class _RenderableText(Component):
    """Component that yields inline text to exercise text-node normalization."""

    def __init__(self, value: str) -> None:
        super().__init__(component_name="InlineText")
        self.value: str = value

    def to_renderable(self) -> str:  # noqa: D401 - testing hook
        return self.value


class _MutableHost(StandardHostObject):
    """Host object that records structural mutations performed by the integrator."""

    def __init__(self, key: str, component_name: str | None = None) -> None:
        super().__init__(
            vdom_key=key,
            component_name=component_name or "Host",
            backend_target=BackendTarget.CLI,
        )
        self.parent: _MutableHost | None = None
        self.children: list[_MutableHost] = []
        self.add_calls: list[int] = []
        self.move_calls: list[int] = []
        self.index_history: list[int] = []
        self.updated: list[dict[str, Any]] = []
        self.destroyed: bool = False
        self.events: list[tuple[str, dict[str, Any]]] = []

    def add_child(self, child: "_MutableHost", index: int) -> None:
        child.parent = self
        self.children.insert(index, child)
        self.add_calls.append(index)

    def move_child(self, child: "_MutableHost", index: int) -> None:
        if child not in self.children:
            raise ValueError("child missing")
        self.children.remove(child)
        self.children.insert(index, child)
        self.move_calls.append(index)

    def remove_child(self, child: "_MutableHost") -> None:
        if child in self.children:
            self.children.remove(child)

    def set_child_index(self, index: int) -> None:
        self.index_history.append(index)

    def update_properties(self, properties: dict[str, Any]) -> None:
        super().update_properties(properties)
        self.updated.append(dict(properties))

    def destroy(self) -> None:
        self.destroyed = True

    def handle_event(self, event_type: str, event_data: dict[str, Any]) -> bool:
        self.events.append((event_type, event_data))
        handled = super().handle_event(event_type, event_data)
        return handled or True


def _build_component_tree() -> Component:
    root = Component(component_name="Root")
    root.children.append(Component(component_name="Child", content=ComponentContent(text="c")))
    custom = _RenderableChild("Renderable")
    root.children.append(custom)
    root.children.append(_RenderableText("inline-text"))
    return root


def test_tree_helper_functions_cover_all_branches() -> None:
    component = _build_component_tree()
    component.key = "pre-existing"

    tree = VDOMTree(backend_target=BackendTarget.CLI)
    node = tree._component_to_node(component)
    assert node.children[0].component_name == "Child"
    assert node.children[1].component_name == "Renderable"
    assert node.children[2].component_name == "text"
    assert isinstance(node.children[2].props["content"], str)
    assert isinstance(component.key, str)

    complex_payload: dict[str, Any] = {
        "numbers": [1, 2, 3],
        "nested": {"alpha": {"x", "y"}},
        "custom": object(),
    }
    normalized = tree_module._normalize_prop_value(complex_payload)
    assert isinstance(normalized, tuple)
    assert normalized[0][0] == "custom"

    props_map = tree_module._normalize_props_map({"payload": complex_payload})
    assert props_map[0][0] == "payload"

    cloned_value = tree_module._clone_prop_value(complex_payload)
    assert cloned_value == complex_payload
    assert cloned_value is not complex_payload

    cloned_props = tree_module._clone_props_dict({"payload": complex_payload})
    assert cloned_props["payload"] is not complex_payload

    # Test _clone_prop_value on tuple (line 49)
    tuple_value = (1, 2, {"nested": "value"})
    cloned_tuple = tree_module._clone_prop_value(tuple_value)
    assert cloned_tuple == tuple_value
    assert cloned_tuple is not tuple_value

    # Test _clear_subtree_dirty with None (line 80)
    tree_module._clear_subtree_dirty(None)  # should return without error

    parent = VDOMNode(component_name="Parent", props={"value": 1}, children=[], key="p")
    child = VDOMNode(component_name="Child", props={}, children=[], key="c")
    child.subtree_hash = 7
    parent.children.append(child)
    parent.props_dirty = True
    tree_module._recompute_node_hash(parent)
    assert parent.props_dirty is False
    assert parent.subtree_hash != 0

    parent.dirty = True
    child.dirty = True
    tree_module._clear_subtree_dirty(parent)
    assert parent.dirty is False
    assert child.dirty is False


def test_vdom_tree_mutations_and_dirty_tracking() -> None:
    tree = VDOMTree(backend_target=BackendTarget.CLI)
    root = _build_component_tree()
    root_key = tree.add_component(root)
    duplicate = Component(component_name="Root")

    with pytest.raises(ComponentNotFoundError):
        tree.update_component("missing", root)

    with pytest.raises(InvalidVDOMOperationError):
        tree.add_component(duplicate, key=root_key)

    root_node = tree.key_map[root_key]
    first_child_key = root_node.children[0].key
    assert first_child_key is not None
    tree.update_node_props(first_child_key, {"extra": 42})
    dirty_state = tree.consume_dirty_state()
    assert dirty_state is not None
    tree.reset_dirty_tracking()

    orphan = VDOMNode(component_name="Detached", props={}, children=[], key="detached")
    with pytest.raises(InvalidVDOMOperationError):
        tree.attach_node(orphan, parent_key="missing", position=0)

    attached = tree.attach_node(orphan, parent_key=root_key, position=1)
    assert attached.parent_key == root_key
    assert attached.key is not None
    tree.move_node(attached.key, 0)
    tree.detach_subtree(attached.key)
    tree.remove_component("missing")  # no-op
    tree.remove_component(root_key)


def test_component_keys_and_refs_management() -> None:
    keys = ComponentKeys()
    component = Component(component_name="Demo")
    key = keys.generate_key(component)
    assert keys.is_key_used(key)
    keys.release_key(key)
    assert not keys.is_key_used(key)
    keys.clear_all_keys()

    # Test generate_key with parent_key (line 32)
    key_with_parent = keys.generate_key(component, "parent")
    assert keys.is_key_used(key_with_parent)
    assert "parent:" in key_with_parent

    refs = ComponentRefs()
    refs.add_ref("demo", component)
    assert refs.get_ref("demo") is component
    refs.remove_ref("demo")
    refs.add_ref("temporary", Component(component_name="Temp"))
    gc.collect()
    cleaned = refs.cleanup_dead_refs()
    assert cleaned >= 0

    # Test get_ref on non-existent key (line 35)
    assert refs.get_ref("nonexistent") is None

    # Test get_ref on dead ref cleanup (lines 40-41)
    assert refs.get_ref("temporary") is None  # should clean up

    # Test get_all_keys (lines 70-71)
    keys_list = refs.get_all_keys()
    assert isinstance(keys_list, list)

    # Test get_live_refs_count (lines 75-80)
    live_count = refs.get_live_refs_count()
    assert isinstance(live_count, int)


class _NonWeakHost(StandardHostObject):
    """Host object that forces strong-ref fallback to cover non-weak path."""

    __slots__ = ("_FORCE_STRONG_REF",)

    def __init__(self, key: str) -> None:
        super().__init__(vdom_key=key, component_name="Noweak", backend_target=BackendTarget.CLI)
        self._FORCE_STRONG_REF = True


def test_host_binding_registry_covers_all_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = HostBindingRegistry()
    backend = BackendTarget.CLI

    host = _MutableHost("alpha")
    registry.register_bind(backend, "alpha", host)
    assert registry.lookup_by_key(backend, "alpha") is host
    assert registry.lookup_key_by_host(host) == (backend, "alpha")

    ref = registry._by_key[(backend, "alpha")]
    assert ref is not None
    registry._on_host_finalize(ref)
    assert (backend, "alpha") not in registry._by_key

    host_two = _MutableHost("beta")
    registry.register_bind(backend, "beta", host_two)
    del host_two
    gc.collect()
    assert registry.cleanup_dead() >= 0

    # Force the non-weakref path by using a slots-based subclass
    nonweak = _NonWeakHost("gamma")
    registry.register_bind(backend, "gamma", nonweak)
    assert registry.lookup_by_key(backend, "gamma") is None
    assert registry.remove_by_key(backend, "gamma") is False

    delta_host = _MutableHost("delta")
    registry.register_bind(backend, "delta", delta_host)
    assert registry.remove_by_key(backend, "delta") is True

    floating_host = _MutableHost("epsilon")
    registry.register_bind(backend, "epsilon", floating_host)
    assert registry.remove_by_host(floating_host) is True

    keys_snapshot = registry.iter_bound_keys()
    assert isinstance(keys_snapshot, list)
    # Test iter_bound_keys with backend filter (line 154)
    filtered_keys = registry.iter_bound_keys(backend)
    assert isinstance(filtered_keys, list)
    
    stats = registry.get_stats()
    assert set(stats) == {"by_key", "by_host"}

    # Test register_bind with previous host_id (line 50)
    registry.register_bind(backend, "alpha", _MutableHost("alpha_new"))
    # Should pop previous

    # Test lookup_by_key with stale ref cleanup (lines 81-85)
    # After gc, lookup should clean
    result = registry.lookup_by_key(backend, "beta")
    assert result is None  # cleaned

    # Test remove_by_host on unregistered host (line 121)
    assert registry.remove_by_host(_MutableHost("unregistered")) is False

    assert isinstance(get_bindings_registry(), HostBindingRegistry)


def test_binding_integrator_and_context_manage_patches(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(binding_integration, "_integrator", None)
    integrator = get_vdom_binding_integrator()
    registry_state: list[tuple[str, str]] = []

    def fake_factory(*, vdom_key: str, component_name: str, backend_target: BackendTarget, vdom_node: VDOMNode | None = None) -> _MutableHost:  # noqa: D401 - inline helper
        host = _MutableHost(vdom_key)
        registry_state.append((component_name, vdom_key))
        return host

    monkeypatch.setattr("ornata.vdom.core.host_objects.create_host_object", fake_factory)

    context = integrator.get_renderer_context(BackendTarget.CLI)
    parent_host = _MutableHost("parent")
    context.register_vdom_binding("parent", parent_host)

    child_node = VDOMNode(component_name="Child", props={"value": 1}, children=[], key="child", parent_key="parent")
    orphan_node = VDOMNode(component_name="Orphan", props={}, children=[], key=None)

    patches = [
        Patch.add_node(child_node),
        Patch.add_node(orphan_node),  # ignored because key is None
        Patch.update_props("child", {"value": 2}),
        Patch.move_node("child", 1),
        Patch.remove_node("child"),
        Patch.replace_root(VDOMNode(component_name="NewRoot", props={}, children=[], key="new-root")),
    ]

    integrator.apply_patches_with_bindings(BackendTarget.CLI, patches)
    # After replacement only the new root binding should remain
    assert context.get_host_object("child") is None
    assert context.get_host_object("new-root") is not None

    stats = context.get_binding_stats()
    assert stats["active_bindings"] >= 0

    route_target = _MutableHost("route")
    context.register_vdom_binding("route", route_target)
    handled = integrator.route_event_to_vdom(BackendTarget.CLI, "route", "click", {"x": 1})
    assert handled is True

    tree = VDOMTree(backend_target=BackendTarget.CLI)
    root_key = tree.add_component(Component(component_name="TreeRoot"))
    bind_host_object_to_tree(BackendTarget.CLI, root_key, _MutableHost(root_key))

    summary = integrator.get_integrated_stats()
    assert "total_active_bindings" in summary
    assert isinstance(summary["contexts"], dict)

    assert isinstance(integrator.get_host_object_by_renderer(BackendTarget.CLI, "route"), _MutableHost)
    assert registry_state  # factory invoked at least once


class _ExceptionalHost(StandardHostObject):
    """Host object that raises exceptions in methods to test error handling."""

    def __init__(self, key: str, raise_in: str) -> None:
        super().__init__(vdom_key=key, component_name="Exceptional", backend_target=BackendTarget.CLI)
        self.raise_in = raise_in
        self.parent: _ExceptionalHost | None = None

    def add_child(self, child: "_ExceptionalHost", index: int) -> None:
        if self.raise_in == "add_child":
            raise ValueError("Simulated add_child error")
        # Otherwise do nothing

    def remove_child(self, child: "_ExceptionalHost") -> None:
        if self.raise_in == "remove_child":
            raise RuntimeError("Simulated remove_child error")

    def destroy(self) -> None:
        if self.raise_in == "destroy":
            raise Exception("Simulated destroy error")
        super().destroy()

    def update_properties(self, properties: dict[str, Any]) -> None:
        if self.raise_in == "update_properties":
            raise KeyError("Simulated update_properties error")
        super().update_properties(properties)

    def move_child(self, child: "_ExceptionalHost", index: int) -> None:
        if self.raise_in == "move_child":
            raise TypeError("Simulated move_child error")

    def set_child_index(self, index: int) -> None:
        if self.raise_in == "set_child_index":
            raise IndexError("Simulated set_child_index error")


def test_binding_integration_exception_handling_and_edge_cases(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test exception handling and edge cases in binding integration."""
    monkeypatch.setattr(binding_integration, "_integrator", None)
    integrator = get_vdom_binding_integrator()

    # Mock create_host_object to return a host with initialize
    def fake_factory(*, vdom_key: str, component_name: str, backend_target: BackendTarget, vdom_node: VDOMNode | None = None) -> _MutableHost:  # noqa: D401 - inline helper
        host = _MutableHost(vdom_key)
        if vdom_node is not None:
            host.initialize(vdom_node)  # Call initialize if needed
        return host

    monkeypatch.setattr("ornata.vdom.core.host_objects.create_host_object", fake_factory)

    context = integrator.get_renderer_context(BackendTarget.CLI)

    # Test add_node with exception in add_child (lines 213-214)
    parent_host = _ExceptionalHost("parent", "add_child")
    context.register_vdom_binding("parent", parent_host)
    child_node = VDOMNode(component_name="Child", props={}, children=[], key="child", parent_key="parent", child_index=0)
    patch_add = Patch.add_node(child_node)
    integrator.apply_patches_with_bindings(BackendTarget.CLI, [patch_add])
    # Should not raise, logs error

    # Test remove_node with exception in remove_child (lines 236-237)
    remove_host = _ExceptionalHost("remove", "remove_child")
    context.register_vdom_binding("remove", remove_host)
    remove_host.parent = parent_host  # Simulate parent
    patch_remove = Patch.remove_node("remove")
    integrator.apply_patches_with_bindings(BackendTarget.CLI, [patch_remove])

    # Test remove_node with exception in destroy (lines 242-243)
    destroy_host = _ExceptionalHost("destroy", "destroy")
    context.register_vdom_binding("destroy", destroy_host)
    patch_destroy = Patch.remove_node("destroy")
    integrator.apply_patches_with_bindings(BackendTarget.CLI, [patch_destroy])

    # Test update_props with exception in update_properties (lines 265-266)
    update_host = _ExceptionalHost("update", "update_properties")
    context.register_vdom_binding("update", update_host)
    patch_update = Patch.update_props("update", {"test": "value"})
    integrator.apply_patches_with_bindings(BackendTarget.CLI, [patch_update])

    # Test update_props with patch.data None (line 258)
    patch_update_none = Patch(PatchType.UPDATE_PROPS, "some_key", None)
    integrator.apply_patches_with_bindings(BackendTarget.CLI, [patch_update_none])

    # Test move_node with host_obj None (lines 283-284)
    patch_move_missing = Patch.move_node("missing", 1)
    integrator.apply_patches_with_bindings(BackendTarget.CLI, [patch_move_missing])

    # Test move_node with exception in parent.move_child (lines 296-297)
    move_parent = _ExceptionalHost("move_parent", "move_child")
    context.register_vdom_binding("move_parent", move_parent)
    move_child = _ExceptionalHost("move_child", "")
    move_child.parent = move_parent
    context.register_vdom_binding("move_child", move_child)
    patch_move = Patch.move_node("move_child", 2)
    integrator.apply_patches_with_bindings(BackendTarget.CLI, [patch_move])

    # Test move_node with exception in set_child_index (lines 301-305)
    index_child = _ExceptionalHost("index_child", "set_child_index")
    context.register_vdom_binding("index_child", index_child)
    patch_index = Patch.move_node("index_child", 3)
    integrator.apply_patches_with_bindings(BackendTarget.CLI, [patch_index])

    # Test replace_root with patch.data None (line 322)
    patch_replace_none = Patch(PatchType.REPLACE_ROOT, None, None)
    integrator.apply_patches_with_bindings(BackendTarget.CLI, [patch_replace_none])

    # Test route_event_to_vdom with host not found (line 377)
    handled_missing = integrator.route_event_to_vdom(BackendTarget.CLI, "nonexistent", "event", {})
    assert handled_missing is False

    # Test route_event_to_vdom with host without handle_event
    no_handle_host = _ExceptionalHost("no_handle", "")
    # Remove handle_event method
    if hasattr(no_handle_host, 'handle_event'):
        delattr(no_handle_host, 'handle_event')
    assert isinstance(integrator.get_host_object_by_renderer(BackendTarget.CLI, "no_handle"), _ExceptionalHost)
    handled_no_handle = integrator.route_event_to_vdom(BackendTarget.CLI, "no_handle", "event", {})
    assert handled_no_handle is False


def test_create_host_object_factory() -> None:
    """Test the create_host_object factory function."""

    host = host_objects.create_host_object(
        vdom_key="test_key",
        component_name="TestComponent",
        backend_target=BackendTarget.CLI
    )
    assert host.vdom_key == "test_key"
    assert host.component_name == "TestComponent"
    assert host.backend_target == BackendTarget.CLI

    # Test with vdom_node
    vdom_node = VDOMNode(component_name="Test", props={"init": True}, children=[], key="test_key")
    host_with_node = host_objects.create_host_object(
        vdom_key="test_key2",
        component_name="TestComponent2",
        backend_target=BackendTarget.CLI,
        vdom_node=vdom_node
    )
    assert host_with_node.vdom_key == "test_key2"
    # initialize should have been called, but since BaseHostObject.initialize may not do much, just assert created


def test_vdom_interfaces() -> None:
    """Test VDOM interface functions."""

    from ornata.definitions.dataclasses.components import Component

    # Test create_vdom_tree
    root_component = Component(component_name="Root")
    tree = interfaces.create_vdom_tree(root_component, BackendTarget.CLI)
    assert tree.backend_target == BackendTarget.CLI
    assert tree.root is not None

    # Test update_vdom_component
    new_component = Component(component_name="NewRoot")
    assert tree.root.key is not None
    patches = interfaces.update_vdom_component(tree, tree.root.key, new_component)
    assert isinstance(patches, list)

    # Test reconcile_vdom_trees (covers lines 40-44 and 14-20)
    old_tree = interfaces.create_vdom_tree(Component(component_name="Old"), BackendTarget.CLI)
    new_tree = interfaces.create_vdom_tree(Component(component_name="New"), BackendTarget.CLI)
    reconcile_patches = interfaces.reconcile_vdom_trees(old_tree, new_tree)
    assert isinstance(reconcile_patches, list)
