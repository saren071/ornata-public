"""Enhanced StandardHostObject protocol implementations for cross-platform VDOM integration.

This module provides comprehensive StandardHostObject protocol implementations that
enable component lifecycle and state management across all rendering backends.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ornata.api.exports.utils import get_logger

if TYPE_CHECKING:
    from ornata.api.exports.definitions import BackendTarget, StandardHostObject, VDOMNode

logger = get_logger(__name__)


# Factory functions for creating platform-specific host objects
def create_host_object(
    vdom_key: str, 
    component_name: str, 
    backend_target: BackendTarget,
    vdom_node: VDOMNode | None = None
) -> StandardHostObject:
    """Create a host object for a VDOM node.
    
    Parameters
    ----------
    vdom_key : str
        The VDOM key for the node.
    component_name : str
        The component name.
    backend_target : BackendTarget
        The backend target.
    vdom_node : VDOMNode | None
        Optional VDOM node for initialization.
        
    Returns
    -------
    StandardHostObject
        A new host object instance.
    """
    from ornata.api.exports.definitions import BaseHostObject
    host_obj = BaseHostObject(
        vdom_key=vdom_key,
        component_name=component_name,
        backend_target=backend_target
    )
    
    if vdom_node is not None:
        host_obj.initialize(vdom_node)
    
    return host_obj