"""Public interfaces for the diffing subsystem."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Patch, VDOMTree


def diff_vdom_trees(old_tree: VDOMTree, new_tree: VDOMTree) -> list[Patch]:
    """Diff two VDOM trees and return patches."""
    from ornata.vdom.diffing.engine import DiffingEngine
    _engine = DiffingEngine()
    return _engine.diff_trees(old_tree, new_tree)


def apply_patches(tree: VDOMTree, patches: list[Patch]) -> VDOMTree:
    """Apply patches to a VDOM tree.
    
    This function applies the given patches to the VDOM tree using the
    TreePatcher, which handles all patch operations including node addition,
    removal, property updates, root replacement, and node movement.
    
    Args:
        tree: The VDOM tree to apply patches to
        patches: List of patches to apply
        
    Returns:
        The same tree object (modified in-place)
    """
    from ornata.vdom.diffing.patcher import TreePatcher
    if not patches:
        return tree

    _patcher = TreePatcher()
    _patcher.apply_patches(tree, patches)
    return tree
