# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
"""Cython helpers accelerating VDOM diff hashing."""

from cpython.dict cimport PyDict_Check

ctypedef long Py_hash_t

def compute_tree_hashes(object root):
    """Return {key: hash} for the subtree rooted at ``root``."""
    cdef dict hashes = {}
    if root is not None:
        _hash_node(root, hashes)
    return hashes

cdef Py_hash_t _hash_node(object node, dict hashes):
    if node is None:
        return 0

    cdef object key = getattr(node, "key", None)
    if key is None:
        return 0

    cdef Py_hash_t node_hash = hash(getattr(node, "component_name", None))
    cdef object props = getattr(node, "props", None)
    if props is not None and PyDict_Check(props):
        for item_key, item_val in sorted(props.items()):
            node_hash ^= hash((item_key, _normalize_hashable(item_val)))

    cdef object children = getattr(node, "children", None)
    if children:
        for child in children:
            node_hash ^= _hash_node(child, hashes)

    hashes[key] = node_hash
    return node_hash

cdef object _normalize_hashable(object value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return tuple(
            (key, _normalize_hashable(val))
            for key, val in sorted(value.items())
        )
    if isinstance(value, (list, tuple)):
        return tuple(_normalize_hashable(item) for item in value)
    if isinstance(value, set):
        return tuple(sorted(_normalize_hashable(item) for item in value))
    return repr(value)


cdef inline dict _coerce_props(object props):
    cdef dict result
    if props is None:
        result = {}
        return result
    if PyDict_Check(props):
        return props
    result = {}
    try:
        result.update(props)
    except Exception:
        pass
    return result


def diff_props(object old_node, object new_node):
    """Compute property differences using a fast loop."""
    cdef dict diffs = {}
    cdef dict old_props = _coerce_props(getattr(old_node, "props", None))
    cdef dict new_props = _coerce_props(getattr(new_node, "props", None))
    cdef object old_norm = getattr(old_node, "_normalized_props", None)
    cdef object new_norm = getattr(new_node, "_normalized_props", None)

    if old_norm is not None and new_norm is not None and old_norm == new_norm:
        return diffs

    cdef object key, new_value
    for key, new_value in new_props.items():
        if key not in old_props or old_props[key] != new_value:
            diffs[key] = new_value
    return diffs


cdef inline bint _nodes_differ(object old_node, object new_node):
    cdef object old_hash = getattr(old_node, "_subtree_hash", None)
    cdef object new_hash = getattr(new_node, "_subtree_hash", None)
    if old_hash is not None and new_hash is not None:
        if old_hash != new_hash:
            return True
        return False

    if getattr(old_node, "component_name", None) != getattr(new_node, "component_name", None):
        return True

    if getattr(old_node, "props", None) != getattr(new_node, "props", None):
        return True

    cdef object old_children = getattr(old_node, "children", None)
    cdef object new_children = getattr(new_node, "children", None)
    if old_children is None and new_children is None:
        return False
    if old_children is None or new_children is None:
        return True
    try:
        if len(old_children) != len(new_children):
            return True
    except Exception:
        if old_children is not new_children:
            return True
    return False


def nodes_differ(object old_node, object new_node):
    """Return True when nodes differ (mirrors Python implementation)."""
    return _nodes_differ(old_node, new_node)


def children_all_keyed(object old_children, object new_children):
    """Return True if all nodes in both groups expose keys."""
    cdef object child
    if old_children:
        for child in old_children:
            if getattr(child, "key", None) is None:
                return False
    if new_children:
        for child in new_children:
            if getattr(child, "key", None) is None:
                return False
    return True


def reconcile_children_keyed(object old_children, object new_children):
    """Return patch instructions for keyed reconciliation (legacy plan)."""
    cdef dict old_map = {}
    cdef set seen = set()
    cdef list instructions = []
    cdef Py_ssize_t idx
    cdef object child
    cdef object key
    cdef object info
    cdef int old_idx
    cdef object old_child

    for idx in range(len(old_children)):
        child = old_children[idx]
        key = getattr(child, "key", None)
        if key is not None:
            old_map[key] = (idx, child)

    for idx in range(len(new_children)):
        child = new_children[idx]
        key = getattr(child, "key", None)
        if key is None:
            continue
        info = old_map.get(key)
        if info is None:
            instructions.append(("add", child))
            continue
        old_idx = info[0]
        old_child = info[1]
        seen.add(key)
        if old_idx != idx:
            instructions.append(("move", key, idx, old_idx))
        if _nodes_differ(old_child, child):
            instructions.append(("diff", old_child, child))

    for key, info in old_map.items():
        if key not in seen:
            instructions.append(("remove", key))

    return instructions


def reconcile_children_keyed_fast(
    object old_children,
    object new_children,
    object add_patch,
    object move_patch,
    object remove_patch,
    object diff_callback,
):
    """Return concrete Patch objects for keyed reconciliation."""
    cdef dict old_map = {}
    cdef set seen = set()
    cdef list patches = []
    cdef Py_ssize_t idx
    cdef object child
    cdef object key
    cdef object info
    cdef int old_idx
    cdef object old_child
    cdef object patch_obj
    cdef object extra_patches

    for idx in range(len(old_children)):
        child = old_children[idx]
        key = getattr(child, "key", None)
        if key is not None:
            old_map[key] = (idx, child)

    for idx in range(len(new_children)):
        child = new_children[idx]
        key = getattr(child, "key", None)
        if key is None:
            continue
        info = old_map.get(key)
        if info is None:
            patch_obj = add_patch(child)
            if patch_obj is not None:
                patches.append(patch_obj)
            continue
        old_idx = info[0]
        old_child = info[1]
        seen.add(key)
        if old_idx != idx:
            patch_obj = move_patch(key, idx)
            if patch_obj is not None:
                patches.append(patch_obj)
        if _nodes_differ(old_child, child):
            extra_patches = diff_callback(old_child, child)
            if extra_patches:
                patches.extend(extra_patches)

    for key, info in old_map.items():
        if key not in seen:
            patch_obj = remove_patch(key)
            if patch_obj is not None:
                patches.append(patch_obj)

    return patches
