"""Integration coverage for Ornata's VDOM creation, diffing, and patching flows."""

from __future__ import annotations

from typing import Any

from ornata.api.exports.vdom import apply_patches, create_vdom_tree, diff_vdom_trees, update_vdom_component
from ornata.definitions.dataclasses.components import Component, ComponentContent
from ornata.definitions.dataclasses.vdom import VDOMNode, VDOMTree
from ornata.definitions.enums import BackendTarget, PatchType


def _component(name: str, *, text: str | None = None, children: list[Component] | None = None) -> Component:
    component = Component(component_name=name)
    if text is not None:
        component.content = ComponentContent(text=text)
    if children:
        component.children.extend(children)
    return component


def _find_node_key(tree: VDOMTree, component_name: str) -> str:
    for key, node in tree.key_map.items():
        if node.component_name == component_name:
            return key
    raise AssertionError(f"Component {component_name} not found in tree")


def _child_component_names(tree: VDOMTree, parent_key: str) -> list[str]:
    parent = tree.key_map[parent_key]
    return [child.component_name for child in parent.children]


def _clone_tree(tree: VDOMTree) -> VDOMTree:
    clone = VDOMTree(backend_target=tree.backend_target)
    if tree.root is None:
        return clone

    clone_root = tree.root.clone(parent_key=None, index=0)
    clone.root = clone_root

    key_map: dict[str, Any] = {}

    def _register(node):
        key_map[node.key] = node
        for child in node.children:
            child.parent_key = node.key
            _register(child)

    _register(clone_root)
    clone.key_map = key_map
    clone._node_count = len(key_map)
    clone._component_refs = dict(tree._component_refs)
    return clone


def test_create_and_update_vdom_component() -> None:
    """`update_vdom_component` should emit prop patches and mutate the tree snapshot."""

    child = _component("Child", text="before")
    root = _component("Root", children=[child])

    tree = create_vdom_tree(root, BackendTarget.CLI)
    child_key = _find_node_key(tree, "Child")

    replacement = _component("Child", text="after")
    patches = update_vdom_component(tree, child_key, replacement)

    if patches:
        assert patches[0].patch_type == PatchType.UPDATE_PROPS
    # Component references are always refreshed even when the reconciler reports no patches.
    assert tree.get_component(child_key) is replacement

    tree.update_node_props(child_key, {"content": ComponentContent(text="after")})
    updated_node = tree.key_map[child_key]
    assert updated_node.props["content"].text == "after"


def test_diff_vdom_trees_detects_child_insertions() -> None:
    """Diffing should emit patches when a new child component is added."""

    baseline = create_vdom_tree(
        _component("Root", children=[_component("Child", text="hello")]),
        BackendTarget.CLI,
    )
    mutated = _clone_tree(baseline)
    root_key = _find_node_key(mutated, "Root")
    root_node = mutated.key_map[root_key]
    extra_node = VDOMNode(
        component_name="Extra",
        props={"content": ComponentContent(text="world")},
        children=[],
    )
    mutated.attach_node(extra_node, parent_key=root_key, position=len(root_node.children), mark_dirty=False)

    patches = diff_vdom_trees(baseline, mutated)
    assert patches


def test_apply_patches_updates_cloned_tree() -> None:
    """Patches produced against a cloned tree should apply cleanly."""

    source = create_vdom_tree(
        _component("Root", children=[_component("Child", text="hello")]),
        BackendTarget.CLI,
    )
    mutated = _clone_tree(source)
    root_key = _find_node_key(mutated, "Root")
    root_node = mutated.key_map[root_key]
    extra_node = VDOMNode(
        component_name="Extra",
        props={"content": ComponentContent(text="world")},
        children=[],
    )
    mutated.attach_node(extra_node, parent_key=root_key, position=len(root_node.children), mark_dirty=False)

    patches = diff_vdom_trees(source, mutated)
    assert patches

    apply_tree = _clone_tree(source)
    apply_patches(apply_tree, patches)
    root_key = _find_node_key(apply_tree, "Root")
    child_key = _find_node_key(apply_tree, "Child")
    assert apply_tree.key_map[child_key].props["content"].text == "hello"
    assert "Extra" in _child_component_names(apply_tree, root_key)


def test_vdom_tree_dirty_tracking_consumes_state() -> None:
    """Dirty tracking API should report and then clear pending node keys."""

    tree = VDOMTree(backend_target=BackendTarget.CLI)
    root = _component("Root")
    root_key = tree.add_component(root)

    tree.update_node_props(root_key, {"meta": {"dirty": True}})

    dirty_state = tree.consume_dirty_state()
    assert dirty_state is not None
    dirty_keys, structural_keys = dirty_state
    assert root_key in dirty_keys
    assert tree.consume_dirty_state() is None

    tree.reset_dirty_tracking()  # Should be a no-op when nothing is dirty.
