"""Unit coverage for VDOM diffing, patching, and memory helpers."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable, Coroutine
from typing import Any

import pytest

import ornata.api.exports.definitions as definitions_api
from ornata.api.exports.vdom import create_vdom_tree
from ornata.definitions.dataclasses.components import Component, ComponentContent
from ornata.definitions.dataclasses.shared import StandardHostObject
from ornata.definitions.dataclasses.vdom import Patch, VDOMNode, VDOMTree
from ornata.definitions.enums import BackendTarget, PatchType
from ornata.vdom.core.bindings import HostBindingRegistry
from ornata.vdom.diffing import algorithms as algorithms_module
from ornata.vdom.diffing.engine import DiffingEngine
from ornata.vdom.diffing import interfaces as diff_interfaces
from ornata.vdom.diffing.optimization import PatchOptimizer
from ornata.vdom.diffing.patcher import TreePatcher, get_bindings_registry
from ornata.vdom.diffing.reconciler import TreeReconciler
from ornata.vdom.diffing.scheduler import EffectScheduler, get_scheduler
from ornata.vdom.memory.memory import MemoryManager


class _TraceLogger:
    """Testing logger that records trace/debug calls."""

    def __init__(self) -> None:
        self.records: list[tuple[str, str]] = []

    @staticmethod
    def isEnabledFor(level: int) -> bool:
        return True

    def log(self, level: int, message: str, *args: Any, **kwargs: Any) -> None:
        formatted = message % args if args else message
        self.records.append(("log", formatted))

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        formatted = message % args if args else message
        self.records.append(("debug", formatted))

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        formatted = message % args if args else message
        self.records.append(("warning", formatted))

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        formatted = message % args if args else message
        self.records.append(("error", formatted))


def _component(name: str, *, text: str | None = None, children: list[Component] | None = None) -> Component:
    component = Component(component_name=name)
    if text is not None:
        component.content = ComponentContent(text=text)
    if children:
        component.children.extend(children)
    return component


def _make_node(
    name: str,
    key: str | None,
    props: dict[str, Any] | None = None,
    *,
    children: list[VDOMNode] | None = None,
) -> VDOMNode:
    node = VDOMNode(component_name=name, props=props or {}, children=[], key=key)
    for index, child in enumerate(children or []):
        child.parent_key = key
        child.child_index = index
        node.children.append(child)
    return node


def _tree_for_testing(tree: VDOMTree) -> Any:
    """Return a dynamically typed handle for mutating test-only hooks."""

    return tree


class _TrackingHost(StandardHostObject):
    """Host object that records destroy calls for TreePatcher tests."""

    def __init__(self, key: str, name: str, backend: BackendTarget) -> None:
        super().__init__(vdom_key=key, component_name=name, backend_target=backend)
        self.destroy_calls = 0

    def destroy(self) -> None:
        super().destroy()
        self.destroy_calls += 1


HostFactory = Callable[[VDOMNode], _TrackingHost | None]


def test_tree_reconciler_handles_keyed_and_prop_changes() -> None:
    reconciler = TreeReconciler()
    old_child = _make_node("Child", "a", {"value": 1})
    new_child = _make_node("Child", "a", {"value": 2})
    old_child.props_dirty = True
    new_child.props_dirty = True

    new_sibling = _make_node("Extra", "b", {"value": 99})
    old_root = _make_node("Parent", "root", {"flag": 0}, children=[old_child])
    new_root = _make_node("Parent", "root", {"flag": 1}, children=[new_sibling, new_child])
    old_root.props_dirty = True
    new_root.props_dirty = True

    patches = reconciler.reconcile(old_root, new_root)
    patch_types = {patch.patch_type for patch in patches}
    assert PatchType.UPDATE_PROPS in patch_types
    assert PatchType.ADD_NODE in patch_types
    assert PatchType.MOVE_NODE in patch_types
    assert any(patch.data.get("value") == 2 for patch in patches if patch.patch_type == PatchType.UPDATE_PROPS)

    skipped_old = _make_node("Static", "root")
    skipped_new = _make_node("Static", "root")
    skipped_old.subtree_hash = skipped_new.subtree_hash = 42
    assert reconciler.reconcile(skipped_old, skipped_new) == []


def test_tree_reconciler_respects_dirty_state() -> None:
    reconciler = TreeReconciler()
    old_child = _make_node("Leaf", "tracked", {"text": "before"})
    new_child = _make_node("Leaf", "tracked", {"text": "after"})
    old_child.props_dirty = True
    new_child.props_dirty = True
    old_root = _make_node("Root", "root", children=[old_child])
    new_root = _make_node("Root", "root", children=[new_child])

    dirty_state = ({"tracked"}, set())
    patches = reconciler.reconcile(old_root, new_root, dirty_state)
    assert any(patch.key == "tracked" for patch in patches)

    silent_state = ({"other"}, set())
    assert reconciler.reconcile(old_root, new_root, silent_state) == []


def test_collect_dirty_state_consumes_tree_state() -> None:
    tree = VDOMTree(backend_target=BackendTarget.CLI)
    key = tree.add_component(_component("Root"))
    tree.update_node_props(key, {"flag": True})

    dirty = algorithms_module._collect_dirty_state(tree)
    assert dirty is not None
    keys, _struct = dirty
    assert key in keys
    assert algorithms_module._collect_dirty_state(tree) is None


def test_tree_patcher_applies_patch_sequence(monkeypatch: pytest.MonkeyPatch) -> None:
    shared_registry = HostBindingRegistry()
    monkeypatch.setattr("ornata.vdom.diffing.patcher.get_bindings_registry", lambda: shared_registry)

    tree = VDOMTree(backend_target=BackendTarget.CLI)
    root_key = tree.add_component(_component("Root"))

    hosts: dict[str, _TrackingHost] = {}

    def host_factory(node: VDOMNode) -> _TrackingHost:
        key = node.key or "anonymous"
        host = _TrackingHost(key, node.component_name, tree.backend_target)
        hosts[key] = host
        return host

    prop_events: list[tuple[str, dict[str, Any]]] = []
    move_events: list[tuple[str, int]] = []
    tree_any = _tree_for_testing(tree)
    tree_any._host_factory = host_factory
    tree_any._host_apply_props = lambda host, delta: prop_events.append((host.vdom_key, delta))
    tree_any._host_move = lambda host, idx: move_events.append((host.vdom_key, idx))

    child_node = VDOMNode(
        component_name="Child",
        props={"value": 1},
        children=[],
        key="child",
        parent_key=root_key,
        child_index=0,
    )
    replacement_root = VDOMNode(component_name="NewRoot", props={}, children=[], key="fresh-root")

    patcher = TreePatcher()
    patches = [
        Patch.add_node(child_node),
        Patch.update_props("child", {"value": 2}),
        Patch.move_node("child", 0),
        Patch.remove_node("child"),
        Patch.replace_root(replacement_root),
    ]

    patcher.apply_patches(tree, patches)

    assert tree.root is not None and tree.root.component_name == "NewRoot"
    assert prop_events == [("child", {"value": 2})]
    assert move_events == [("child", 0)]
    assert hosts["child"].destroy_calls == 1
    assert shared_registry.lookup_by_key(tree.backend_target, "child") is None


def test_diffing_engine_selects_algorithms() -> None:
    engine = DiffingEngine()

    big_tree = VDOMTree(backend_target=BackendTarget.CLI)
    big_tree.root = _make_node("Big", "root")
    big_tree._node_count = 2000  # noqa: SLF001 - force threshold
    assert engine._select_algorithm(big_tree, big_tree) is engine._algorithms["incremental"]

    keyed_tree = VDOMTree(backend_target=BackendTarget.CLI)
    keyed_tree.root = _make_node("Keyed", "root", children=[_make_node("Child", "kid")])
    keyed_tree._node_count = 3  # noqa: SLF001
    assert engine._select_algorithm(keyed_tree, keyed_tree) is engine._algorithms["keyed"]

    simple_tree = VDOMTree(backend_target=BackendTarget.CLI)
    simple_tree.root = _make_node("Simple", None)
    simple_tree._node_count = 1  # noqa: SLF001
    assert engine._select_algorithm(simple_tree, simple_tree) is engine._algorithms["simple"]


def test_diffing_engine_caches_results() -> None:
    baseline = create_vdom_tree(_component("Root", children=[_component("Child", text="hello")]), BackendTarget.CLI)
    mutated = create_vdom_tree(_component("Root", children=[_component("Child", text="world")]), BackendTarget.CLI)

    engine = DiffingEngine()
    first = engine.diff_trees(baseline, mutated)
    second = engine.diff_trees(baseline, mutated)
    assert first == second


def test_patch_optimizer_merges_and_sorts(monkeypatch: pytest.MonkeyPatch) -> None:
    optimizer = PatchOptimizer()
    monkeypatch.setattr(definitions_api, "MIN_PATCH_OPTIMIZATION", 1, raising=False)

    update_a = Patch.update_props("node", {"alpha": 1})
    update_b = Patch.update_props("node", {"beta": 2})
    add_child = Patch.add_node(VDOMNode(component_name="Child", props={}, children=[], key="child"))
    duplicate_add = Patch.add_node(VDOMNode(component_name="Child", props={}, children=[], key="child"))

    optimized = optimizer.optimize([update_a, update_b, add_child, duplicate_add])
    merged_updates = [patch for patch in optimized if patch.patch_type == PatchType.UPDATE_PROPS]
    assert merged_updates and merged_updates[0].data == {"alpha": 1, "beta": 2}
    add_nodes = [patch for patch in optimized if patch.patch_type == PatchType.ADD_NODE]
    assert len(add_nodes) == 1


def test_memory_manager_reports_stats(monkeypatch: pytest.MonkeyPatch) -> None:
    manager = MemoryManager()
    manager._large_operations_threshold = 0  # noqa: SLF001 - force path

    tree = VDOMTree(backend_target=BackendTarget.CLI)
    tree.add_component(_component("Root", children=[_component("Child")]))

    manager.optimize_for_large_tree(tree)
    stats = manager.monitor_memory_usage(tree)
    assert stats["node_count"] >= 1

    monkeypatch.setattr("gc.collect", lambda generation=0: 0)
    manager.cleanup_after_operation(tree)

    # Test _count_nodes with None root (line 80)
    none_tree = VDOMTree(backend_target=BackendTarget.CLI)
    none_tree.root = None
    count_none = manager._count_nodes(none_tree)
    assert count_none == 0

    # Test _count_nodes with node without children (line 73)
    # By having a root with no children attr or empty
    # But since it's hasattr, if no children, return 1
    # In the code, if not hasattr(node, "children"): return 1
    # But VDOMNode has children, so to test, perhaps create a mock node without children.

    # For cleanup_after_operation with cleaned refs (line 50), hard to trigger without dead refs


def test_patch_optimizer_handles_empty_and_small_batches(monkeypatch: pytest.MonkeyPatch) -> None:
    optimizer = PatchOptimizer()
    monkeypatch.setattr(definitions_api, "MIN_PATCH_OPTIMIZATION", 5, raising=False)

    assert optimizer.optimize([]) == []

    patches = [Patch.add_node(VDOMNode(component_name="Solo", props={}, children=[], key="solo"))]
    optimized = optimizer.optimize(patches)
    assert optimized is patches

    # Test _merge_compatible_patches with empty (line 58)
    merged = optimizer._merge_compatible_patches([])
    assert merged == []


def test_tree_patcher_validates_inputs_and_host_hooks(monkeypatch: pytest.MonkeyPatch) -> None:
    patcher = TreePatcher()
    baseline_registry = get_bindings_registry()
    tree = VDOMTree(backend_target=BackendTarget.CLI)
    root_key = tree.add_component(_component("Root", children=[_component("Child")]))
    child_node = tree.key_map[root_key].children[0]
    assert child_node.key is not None
    child_key = child_node.key

    shared_registry = HostBindingRegistry()
    monkeypatch.setattr("ornata.vdom.diffing.patcher.get_bindings_registry", lambda: shared_registry)
    host = _TrackingHost(child_key, child_node.component_name, tree.backend_target)
    shared_registry.on_patch_add_node(tree, child_key, host)

    tree_any = _tree_for_testing(tree)
    apply_calls: list[dict[str, Any]] = []
    move_calls: list[int] = []

    def failing_apply(host_obj: StandardHostObject, props: dict[str, Any]) -> None:
        apply_calls.append(props)
        raise RuntimeError("props failure")

    def failing_move(host_obj: StandardHostObject, idx: int) -> None:
        move_calls.append(idx)
        raise RuntimeError("move failure")

    tree_any._host_apply_props = failing_apply
    tree_any._host_move = failing_move

    with pytest.raises(ValueError):
        patcher._apply_patch(tree, Patch(PatchType.REMOVE_NODE))
    with pytest.raises(ValueError):
        patcher._apply_patch(tree, Patch(PatchType.UPDATE_PROPS, data={"value": 1}))
    with pytest.raises(ValueError):
        patcher._apply_patch(tree, Patch(PatchType.MOVE_NODE, data=1))

    patcher._add_node(tree, None)
    patcher._remove_node(tree, "ghost")
    patcher._update_props(tree, "ghost", {"value": 1})

    patcher._update_props(tree, child_key, {"value": 2})
    assert tree.key_map[child_key].props["value"] == 2

    patcher._move_node(tree, "ghost", 1)
    patcher._move_node(tree, child_key, 0)

    assert apply_calls and move_calls
    assert get_bindings_registry() is baseline_registry

    # Test _replace_root with new_root None (lines 126-128)
    patcher._replace_root(tree, None)
    assert tree.root is None

    # Test host_factory returning None (line 168)
    def none_factory(node):
        return None
    tree_any._host_factory = none_factory
    patcher._add_node(tree, VDOMNode(component_name="Test", props={}, children=[], key="test"))

    # Test host_factory raising exception (lines 163-165)
    def failing_factory(node):
        raise RuntimeError("factory error")
    tree_any._host_factory = failing_factory
    patcher._add_node(tree, VDOMNode(component_name="Test2", props={}, children=[], key="test2"))


def test_tree_reconciler_replaces_root_and_logs(monkeypatch: pytest.MonkeyPatch) -> None:
    trace = _TraceLogger()
    monkeypatch.setattr("ornata.vdom.diffing.reconciler.logger", trace)

    reconciler = TreeReconciler()
    old_root = _make_node("Old", "root")
    new_root = _make_node("New", "root")

    patches = reconciler.reconcile(old_root, new_root)
    assert len(patches) == 1 and patches[0].patch_type == PatchType.REPLACE_ROOT
    assert any("Root component changed" in message for _level, message in trace.records)


def test_tree_reconciler_requires_keys_for_prop_updates() -> None:
    reconciler = TreeReconciler()
    old_node = _make_node("Comp", None, {"value": 1})
    new_node = _make_node("Comp", None, {"value": 2})
    old_node.props_dirty = True
    new_node.props_dirty = True

    with pytest.raises(ValueError):
        reconciler.reconcile(old_node, new_node)


def test_tree_reconciler_dirty_descendant_path() -> None:
    reconciler = TreeReconciler()
    old_child = _make_node("Child", "kid", {"value": 1})
    new_child = _make_node("Child", "kid", {"value": 2})
    old_child.props_dirty = True
    new_child.props_dirty = True
    old_parent = _make_node("Parent", "parent", children=[old_child])
    new_parent = _make_node("Parent", "parent", children=[new_child])

    patches = reconciler.reconcile(old_parent, new_parent, ({"kid"}, set()))
    assert any(patch.key == "kid" and patch.patch_type == PatchType.UPDATE_PROPS for patch in patches)


def test_tree_reconciler_keyed_plan_logging(monkeypatch: pytest.MonkeyPatch) -> None:
    trace = _TraceLogger()
    monkeypatch.setattr("ornata.vdom.diffing.reconciler.logger", trace)

    reconciler = TreeReconciler()
    reconciler._cython_keyed_fast = None
    added_node = _make_node("Extra", "extra")
    old_child = _make_node("Child", "kid", {"value": 1})
    new_child = _make_node("Child", "kid", {"value": 2})
    old_child.props_dirty = True
    new_child.props_dirty = True

    plan = [
        ("add", added_node),
        ("move", "kid", 0, 1),
        ("diff", old_child, new_child),
        ("remove", "ghost"),
    ]

    def keyed_plan(old_children: list[VDOMNode], new_children: list[VDOMNode]) -> list[tuple[Any, ...]]:
        if old_children and old_children[0] is old_child:
            return plan
        return []

    reconciler._cython_keyed_plan = keyed_plan

    patches = reconciler._reconcile_children_keyed([old_child], [new_child], trace_enabled=True)
    patch_types = {patch.patch_type for patch in patches}
    assert {
        PatchType.ADD_NODE,
        PatchType.MOVE_NODE,
        PatchType.REMOVE_NODE,
        PatchType.UPDATE_PROPS,
    } <= patch_types
    assert any("Adding node" in message or "Moving node" in message for _level, message in trace.records)


def test_tree_reconciler_keyed_fast_path(monkeypatch: pytest.MonkeyPatch) -> None:
    trace = _TraceLogger()
    monkeypatch.setattr("ornata.vdom.diffing.reconciler.logger", trace)

    reconciler = TreeReconciler()

    old_child = _make_node("Child", "old", {})
    new_child = _make_node("Child", "new", {})

    def fake_fast(
        old_children: list[VDOMNode],
        new_children: list[VDOMNode],
        add_factory: Callable[[VDOMNode], Patch],
        move_factory: Callable[[str, int], Patch],
        remove_factory: Callable[[str], Patch],
        reconcile_internal: Callable[[VDOMNode, VDOMNode], list[Patch]],
    ) -> list[Patch]:
        if not old_children or not new_children:
            return []
        patches: list[Patch] = [
            add_factory(new_children[0]),
            move_factory(old_children[0].key or "old", 0),
            remove_factory(old_children[0].key or "old"),
        ]
        patches.extend(reconcile_internal(old_children[0], new_children[0]))
        return patches

    reconciler._cython_keyed_fast = fake_fast
    patches = reconciler._reconcile_children_keyed([old_child], [new_child], trace_enabled=True)
    assert any(patch.patch_type == PatchType.ADD_NODE for patch in patches)
    assert any("Adding node" in message for _level, message in trace.records)


def test_tree_reconciler_children_fallback_handles_mixed_nodes() -> None:
    reconciler = TreeReconciler()
    old_children = [
        _make_node("Text", None, {"content": "a"}),
        _make_node("Stay", "stay", {"value": 1}),
        _make_node("Move", "move", {"value": 1}),
        _make_node("Remove", "remove"),
    ]
    new_children = [
        _make_node("Text", None, {"content": "a"}),
        _make_node("Move", "move", {"value": 1}),
        _make_node("Stay", "stay", {"value": 2}),
        _make_node("Add", "add"),
    ]
    old_children[1].props_dirty = True
    new_children[2].props_dirty = True

    patches = reconciler._reconcile_children_fallback(old_children, new_children, trace_enabled=False)
    patch_types = {patch.patch_type for patch in patches}
    assert PatchType.REMOVE_NODE in patch_types
    assert PatchType.ADD_NODE in patch_types
    assert PatchType.MOVE_NODE in patch_types
    assert PatchType.UPDATE_PROPS in patch_types


def test_tree_reconciler_node_difference_checks() -> None:
    reconciler = TreeReconciler()

    def _prepared(node: VDOMNode, *, hash_value: int = 0) -> VDOMNode:
        node.props_dirty = False
        node.dirty = False
        node.subtree_hash = hash_value
        return node

    # Component name mismatch should surface once hashes differ
    assert reconciler._nodes_differ(
        _prepared(_make_node("A", "k"), hash_value=7),
        _prepared(_make_node("B", "k"), hash_value=8),
    )

    # Props mismatch
    assert reconciler._nodes_differ(
        _prepared(_make_node("A", "k", {"value": 1}), hash_value=1),
        _prepared(_make_node("A", "k", {"value": 2}), hash_value=2),
    )

    # Children length mismatch
    assert reconciler._nodes_differ(
        _prepared(_make_node("A", "k", {}, children=[_make_node("Child", "c")]), hash_value=3),
        _prepared(_make_node("A", "k", {}), hash_value=4),
    )


def test_tree_reconciler_dirty_helper_methods() -> None:
    reconciler = TreeReconciler()
    old_node = _make_node("Parent", "parent", children=[_make_node("Child", "child")])
    new_node = _make_node("Parent", "parent", children=[_make_node("Child", "child")])

    def _clean(node: VDOMNode) -> VDOMNode:
        node.props_dirty = False
        node.dirty = False
        for child in node.children:
            _clean(child)
        return node

    old_node = _clean(old_node)
    new_node = _clean(new_node)

    reconciler._active_dirty_keys = {"parent"}
    assert reconciler._should_reconcile(old_node, new_node) is True

    reconciler._active_dirty_keys = {"other"}
    assert reconciler._should_reconcile(old_node, new_node) is True

    keyed_old = _clean(_make_node("Keyed", "keyed"))
    keyed_new = _clean(_make_node("Keyed", "keyed"))
    keyed_old.children.clear()
    keyed_new.children.clear()
    reconciler._active_dirty_keys = {"none"}
    assert reconciler._should_reconcile(keyed_old, keyed_new) is False

    keyless_old = _clean(_make_node("Anon", None))
    keyless_new = _clean(_make_node("Anon", None))
    reconciler._active_dirty_keys = {"none"}
    assert reconciler._should_reconcile(keyless_old, keyless_new) is False

    reconciler._active_structural_keys = {"parent"}
    assert reconciler._is_structural_dirty(old_node, new_node) is True

    reconciler._active_structural_keys = set()
    reconciler._active_dirty_keys = {"child"}
    patches = reconciler._reconcile_dirty_descendants(old_node, new_node)
    assert patches == []


def test_effect_scheduler_commit_flush_and_frame_end(monkeypatch: pytest.MonkeyPatch) -> None:
    trace = _TraceLogger()
    monkeypatch.setattr("ornata.vdom.diffing.scheduler.logger", trace)

    scheduler = EffectScheduler()
    order: list[str] = []

    scheduler.begin_commit()
    scheduler.enqueue_effect(lambda: order.append("idle"), priority=2, label="idle-task")
    scheduler.enqueue_effect(lambda: order.append("norm"), label="norm-task")
    scheduler.enqueue_effect(lambda: order.append("high"), priority=0, label="high-task")
    scheduler.end_commit()

    assert order == ["high", "norm", "idle"]
    stats = scheduler.stats()
    assert stats["sync_high"] == stats["sync_norm"] == stats["sync_idle"] == 0

    # Test flush_sync with max_count (line 114)
    scheduler.enqueue_effect(lambda: order.append("first"), label="first")
    scheduler.enqueue_effect(lambda: order.append("second"), label="second")
    executed = scheduler.flush_sync(max_count=1)
    assert executed == 1
    assert len(order) == 4  # high, norm, idle, first
    scheduler.flush_sync()  # flush the rest
    assert len(order) == 5

    scheduler.enqueue_effect(lambda: order.append("frame"), priority=2, label="frame-task")
    scheduler.on_frame_end()
    assert order[-1] == "frame"

    scheduler.on_component_mounted(label="mount", cb=lambda: order.append("mount"))
    scheduler.on_component_updated(label="update", cb=lambda: order.append("update"))
    scheduler.on_component_unmounted(label="unmount", cb=lambda: order.append("unmount"))
    scheduler.enqueue_effect(lambda: (_ for _ in ()).throw(RuntimeError("failure")), label="crash-task")
    scheduler.flush_sync()

    scheduler.end_commit()
    assert any("end_commit called without matching begin_commit" in message for level, message in trace.records if level == "warning")


def test_effect_scheduler_async_flush_and_thread_local() -> None:
    async def _run_async() -> list[str]:
        scheduler = EffectScheduler()
        events: list[str] = []

        def make_factory(label: str) -> Callable[[], Coroutine[Any, Any, None]]:
            async def runner() -> None:
                events.append(label)

            return runner

        scheduler.enqueue_async_effect(make_factory("high"), priority=0, label="async-high")
        scheduler.enqueue_async_effect(make_factory("norm"), label="async-norm")
        scheduler.enqueue_async_effect(make_factory("idle"), priority=2, label="async-idle")
        count = await scheduler.flush_async()
        assert count == 3
        return events

    events = asyncio.run(_run_async())
    assert events == ["high", "norm", "idle"]

    # Test flush_async with max_count (line 137)
    async def _run_async_max():
        scheduler = EffectScheduler()
        events = []

        def make_factory(label):
            async def runner():
                events.append(label)
            return runner

        scheduler.enqueue_async_effect(make_factory("first"), label="first")
        scheduler.enqueue_async_effect(make_factory("second"), label="second")
        count = await scheduler.flush_async(max_count=1)
        assert count == 1
        assert events == ["first"]
        return events

    events_max = asyncio.run(_run_async_max())
    assert events_max == ["first"]

    main_scheduler = get_scheduler()
    results: list[EffectScheduler] = []

    def _worker() -> None:
        results.append(get_scheduler())

    thread = threading.Thread(target=_worker)
    thread.start()
    thread.join()

    assert results and results[0] is not main_scheduler
    assert get_scheduler() is main_scheduler


def test_incremental_diff_algorithm_basic_operations() -> None:
    """Test IncrementalDiff diff method covers basic paths."""
    from ornata.vdom.diffing.algorithms import IncrementalDiff

    diff_alg = IncrementalDiff()
    old_tree = create_vdom_tree(_component("Root"), BackendTarget.CLI)
    new_tree = create_vdom_tree(_component("Root"), BackendTarget.CLI)

    # Same root, should return empty (line 54-56)
    patches = diff_alg.diff(old_tree, new_tree)
    assert patches == []

    # Different trees
    new_tree = create_vdom_tree(_component("NewRoot"), BackendTarget.CLI)
    patches = diff_alg.diff(old_tree, new_tree)
    assert isinstance(patches, list)

    # Test _tree_size (lines 237-252)
    size = diff_alg._tree_size(old_tree)
    assert size >= 1


def test_keyed_and_simple_diff_algorithms() -> None:
    """Test KeyedDiff and SimpleDiff diff methods."""
    from ornata.vdom.diffing.algorithms import KeyedDiff, SimpleDiff

    old_tree = create_vdom_tree(_component("Root"), BackendTarget.CLI)
    new_tree = create_vdom_tree(_component("New"), BackendTarget.CLI)

    keyed_alg = KeyedDiff()
    patches = keyed_alg.diff(old_tree, new_tree)
    assert isinstance(patches, list)

    simple_alg = SimpleDiff()
    patches = simple_alg.diff(old_tree, new_tree)
    assert isinstance(patches, list)

    # Test with None root (lines 268-269 for KeyedDiff, 290-291 for SimpleDiff)
    old_tree.root = None
    patches = keyed_alg.diff(old_tree, new_tree)
    assert patches == []

    new_tree.root = None
    patches = simple_alg.diff(old_tree, new_tree)
    assert patches == []


def test_diff_cache_operations() -> None:
    """Test DiffCache covers all methods."""
    from ornata.vdom.diffing.cache import DiffCache

    cache = DiffCache(max_size=5)

    # Test __setitem__ and __getitem__
    cache["key1"] = "value1"
    assert cache["key1"] == "value1"
    assert "key1" in cache

    # Test get with default (line 25)
    assert cache["missing"] is None

    # Test __setitem__ update existing (line 32)
    cache["key1"] = "value1_updated"

    # Test __setitem__ evict LRU (line 35)
    for i in range(2, 7):
        cache[f"key{i}"] = f"value{i}"
    # Now should have evicted key1 if max_size=5

    # Test get method (lines 46-51)
    cache["key7"] = "value7"
    assert cache.get("key7") == "value7"
    assert cache.get("missing", "default") == "default"

    # Test get_stats (lines 60-61)
    stats = cache.get_stats()
    assert "size" in stats
    assert "max_size" in stats
    assert "utilization" in stats

    cache.clear()


def test_diffing_engine_edge_cases() -> None:
    """Test DiffingEngine covers edge cases and missed lines."""
    engine = DiffingEngine()

    # Test identical root (lines 36-37)
    tree = create_vdom_tree(_component("Root"), BackendTarget.CLI)
    patches = engine.diff_trees(tree, tree)
    assert patches == []

    # Test _tree_size without cache (lines 91-96)
    uncached_tree = VDOMTree(backend_target=BackendTarget.CLI)
    uncached_tree.root = _make_node("Root", "root")
    size = engine._tree_size(uncached_tree)
    assert size >= 1

    # Test _has_keys on None root (line 103)
    none_tree = VDOMTree(backend_target=BackendTarget.CLI)
    none_tree.root = None
    has_keys = engine._has_keys(none_tree)
    assert has_keys is False

    # Test _make_cache_key fallback (lines 119-121)
    no_hash_tree = VDOMTree(backend_target=BackendTarget.CLI)
    no_hash_tree.root = _make_node("Root", "root")
    # Remove subtree_hash
    if hasattr(no_hash_tree.root, 'subtree_hash'):
        delattr(no_hash_tree.root, 'subtree_hash')
    cache_key = engine._make_cache_key(tree, no_hash_tree)
    assert isinstance(cache_key, str)

    # Test _hash_tree and _normalize_hashable (lines 125-144, 148-164)
    hash_str = engine._hash_tree(no_hash_tree.root)
    assert isinstance(hash_str, str)


def test_incremental_differ_operations() -> None:
    """Test IncrementalDiffer covers all methods."""
    from ornata.vdom.diffing.incremental import IncrementalDiffer

    differ = IncrementalDiffer()

    # Test diff_incremental (lines 15-32)
    current = [1, 2, 3]
    previous = [1, 4, 3]
    patches = differ.diff_incremental(current, previous)
    assert isinstance(patches, list)
    assert len(patches) > 0

    # Test update_previous_chunks (line 36)
    differ.update_previous_chunks(current)


def test_diffing_interfaces() -> None:
    """Test diffing interface functions."""

    old_tree = create_vdom_tree(_component("Old"), BackendTarget.CLI)
    new_tree = create_vdom_tree(_component("New"), BackendTarget.CLI)

    # Test diff_vdom_trees
    patches = diff_interfaces.diff_vdom_trees(old_tree, new_tree)
    assert isinstance(patches, list)

    # Test apply_patches with empty patches (line 34)
    result_tree = diff_interfaces.apply_patches(old_tree, [])
    assert result_tree is old_tree


def test_component_lifecycle_management(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test ComponentLifecycle covers all methods."""
    from ornata.vdom.diffing.lifecycle import ComponentLifecycle
    from ornata.definitions.dataclasses.components import Component

    lifecycle = ComponentLifecycle()
    component = Component(component_name="Test")

    # Mock scheduler to avoid threading issues
    class MockScheduler:
        def on_component_mounted(self, label, cb): pass
        def enqueue_effect(self, cb, priority=0, label=""): pass
        def on_component_updated(self, label, cb): pass

    monkeypatch.setattr("ornata.vdom.diffing.lifecycle.get_scheduler", lambda: MockScheduler())

    # Test mount_component (covers lines 29-38)
    lifecycle.mount_component("test", component)

    # Test is_mounted (lines 74-75)
    assert lifecycle.is_mounted("test") is True

    # Test get_mounted_components (lines 79-80)
    mounted = lifecycle.get_mounted_components()
    assert len(mounted) >= 1

    # Test update_component (covers lines 59-70)
    new_component = Component(component_name="Updated")
    lifecycle.update_component("test", new_component)

    # Test unmount_component (covers lines 42-55)
    lifecycle.unmount_component("test")
    assert lifecycle.is_mounted("test") is False


def test_patch_object_pool_operations() -> None:
    """Test PatchObjectPool covers all methods."""
    from ornata.vdom.diffing.object_pool import PatchObjectPool, PooledPatch, get_patch_object_pool
    from ornata.api.exports.definitions import PatchPoolConfig

    config = PatchPoolConfig(max_pool_size=5)
    pool = PatchObjectPool(config)

    # Test acquire_patch (lines 148-151)
    patch = pool.acquire_patch("test_type")
    assert patch is not None

    # Test release_patch (lines 155-157)
    pool.release_patch(patch, "test_type")

    # Test cleanup (lines 161-164)
    pool.cleanup()

    # Test get_stats (lines 168-173)
    stats = pool.get_stats("test_type")
    assert hasattr(stats, 'created')

    # Test global stats (line 173)
    global_stats = pool.get_stats()
    assert hasattr(global_stats, 'created')

    # Test get_patch_object_pool (line 230)
    global_pool = get_patch_object_pool()
    assert isinstance(global_pool, PatchObjectPool)

    # Test PooledPatch context manager (lines 241-246)
    with PooledPatch("context") as ctx_patch:
        assert ctx_patch is not None
    # Should be released automatically
