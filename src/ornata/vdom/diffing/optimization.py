"""Patch optimization for diffing operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ornata.api.exports.definitions import Patch, PatchType


class PatchOptimizer:
    """Optimizes patches to reduce rendering overhead."""

    def optimize(self, patches: list[Patch]) -> list[Patch]:
        """Optimize a list of patches."""
        from ornata.api.exports.definitions import MIN_PATCH_OPTIMIZATION
        if not patches:
            return patches

        if len(patches) < MIN_PATCH_OPTIMIZATION:
            return patches

        # Remove redundant patches
        optimized = self._remove_redundant_patches(patches)

        # Merge compatible patches
        optimized = self._merge_compatible_patches(optimized)

        # Sort patches for efficient application
        optimized = self._sort_patches(optimized)

        return optimized

    def _remove_redundant_patches(self, patches: list[Patch]) -> list[Patch]:
        """Remove patches that cancel each other out."""
        from ornata.api.exports.definitions import Patch, PatchType
        seen: dict[tuple[str, str | None], Patch] = {}
        for patch in patches:
            map_key = (patch.patch_type.value, patch.key)
            if patch.patch_type == PatchType.UPDATE_PROPS and patch.key is not None:
                existing = seen.get(map_key)
                if existing is None:
                    # Preserve original ordering by storing first occurrence and cloning its data
                    merged = Patch.update_props(patch.key, dict(patch.data or {}))
                    seen[map_key] = merged
                else:
                    existing_props = existing.data or {}
                    existing_props.update(patch.data or {})
                    existing.data = existing_props
                continue
            seen[map_key] = patch
        return list(seen.values())

    def _merge_compatible_patches(self, patches: list[Patch]) -> list[Patch]:
        """Merge patches that can be combined."""
        from ornata.api.exports.definitions import Patch, PatchType
        if not patches:
            return patches
            
        # Group patches by type and key for merging
        patch_groups: dict[tuple[PatchType, str | None], list[Patch]] = {}
        
        for patch in patches:
            group_key: tuple[PatchType, str | None] = (patch.patch_type, patch.key)
            if group_key not in patch_groups:
                patch_groups[group_key] = []
            patch_groups[group_key].append(patch)
        
        merged_patches: list[Patch] = []
        
        for group_key, group_patches in patch_groups.items():
            patch_type, key = group_key
            
            if patch_type == PatchType.UPDATE_PROPS and key is not None:
                # Merge multiple UPDATE_PROPS patches for the same key
                merged_props: dict[str, Any] = {}
                for patch in group_patches:
                    merged_props.update(patch.data)
                
                # Create a single merged patch
                if merged_props:
                    merged_patches.append(Patch.update_props(key, merged_props))
            else:
                # For other patch types, keep as-is (can't merge safely)
                merged_patches.extend(group_patches)
        
        return merged_patches

    def _sort_patches(self, patches: list[Patch]) -> list[Patch]:
        """Sort patches for optimal application order."""
        from ornata.api.exports.definitions import PatchType
        # Sort by operation type priority
        priority = {
            PatchType.REMOVE_NODE: 0,
            PatchType.ADD_NODE: 1,
            PatchType.MOVE_NODE: 2,
            PatchType.UPDATE_PROPS: 3,
            PatchType.REPLACE_ROOT: 4,
        }

        return sorted(patches, key=lambda p: priority.get(p.patch_type, 999))
