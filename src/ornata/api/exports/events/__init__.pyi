"""Type stubs for the events subsystem exports."""

from __future__ import annotations

from ornata.events import handlers as handlers
from ornata.events import history as history
from ornata.events import processing as processing
from ornata.events.core import bus as bus
from ornata.events.core import subsystem as subsystem
from ornata.events.core.bus import EventBus as EventBus
from ornata.events.core.bus import GlobalEventBus as GlobalEventBus
from ornata.events.core.bus import LockFreeEventQueue as LockFreeEventQueue
from ornata.events.core.bus import SubsystemEventBus as SubsystemEventBus
from ornata.events.core.object_pool import EventObjectPool as EventObjectPool
from ornata.events.core.object_pool import EventPool as EventPool
from ornata.events.core.object_pool import EventPoolConfig as EventPoolConfig
from ornata.events.core.object_pool import EventPoolStats as EventPoolStats
from ornata.events.core.object_pool import PooledComponentEvent as PooledComponentEvent
from ornata.events.core.object_pool import PooledEvent as PooledEvent
from ornata.events.core.object_pool import PooledKeyEvent as PooledKeyEvent
from ornata.events.core.object_pool import PooledMouseEvent as PooledMouseEvent
from ornata.events.core.object_pool import get_event_object_pool as get_event_object_pool
from ornata.events.core.object_pool import pooled_component_event as pooled_component_event
from ornata.events.core.object_pool import pooled_event as pooled_event
from ornata.events.core.object_pool import pooled_key_event as pooled_key_event
from ornata.events.core.object_pool import pooled_mouse_event as pooled_mouse_event
from ornata.events.core.subsystem import EventSubsystem as EventSubsystem
from ornata.events.core.subsystem import add_event_listener as add_event_listener  #type: ignore
from ornata.events.core.subsystem import create_event_subsystem as create_event_subsystem
from ornata.events.core.subsystem import dispatch_cross_subsystem_event as dispatch_cross_subsystem_event  #type: ignore
from ornata.events.handlers.handlers import EventHandler as EventHandler
from ornata.events.handlers.handlers import EventHandlerManager as EventHandlerManager
from ornata.events.handlers.handlers import EventHandlerWrapper as EventHandlerWrapper
from ornata.events.history import replay as replay
from ornata.events.history.replay import EventEntry as EventEntry
from ornata.events.history.replay import EventReplayAnalyzer as EventReplayAnalyzer
from ornata.events.history.replay import EventReplayBuffer as EventReplayBuffer
from ornata.events.history.replay import EventReplayer as EventReplayer
from ornata.events.history.replay import create_event_replayer as create_event_replayer
from ornata.events.history.replay import create_replay_analyzer as create_replay_analyzer
from ornata.events.history.replay import create_replay_buffer as create_replay_buffer
from ornata.events.platform import factory as factory
from ornata.events.platform.cli import CliEventHandler as CliEventHandler
from ornata.events.platform.cli import create_cli_handler as create_cli_handler
from ornata.events.platform.factory import PlatformEventHandler as PlatformEventHandler
from ornata.events.platform.factory import create_platform_handler as create_platform_handler
from ornata.events.platform.windows import WindowsEventHandler as WindowsEventHandler
from ornata.events.platform.windows import create_windows_handler as create_windows_handler
from ornata.events.processing import async_processor as async_processor
from ornata.events.processing import filtering as filtering
from ornata.events.processing import propagation as propagation
from ornata.events.processing.async_processor import AsyncEventProcessor as AsyncEventProcessor
from ornata.events.processing.async_processor import BatchedEventProcessor as BatchedEventProcessor
from ornata.events.processing.async_processor import EventQueue as EventQueue
from ornata.events.processing.filtering import EventDropFilter as EventDropFilter
from ornata.events.processing.filtering import EventFilter as EventFilter
from ornata.events.processing.filtering import EventFilterManager as EventFilterManager
from ornata.events.processing.filtering import EventFilterWrapper as EventFilterWrapper
from ornata.events.processing.filtering import EventModifyFilter as EventModifyFilter
from ornata.events.processing.filtering import EventThrottleFilter as EventThrottleFilter
from ornata.events.processing.filtering import EventTransformer as EventTransformer
from ornata.events.processing.filtering import create_drop_filter as create_drop_filter  #type: ignore
from ornata.events.processing.filtering import create_modify_filter as create_modify_filter  #type: ignore
from ornata.events.processing.filtering import create_throttle_filter as create_throttle_filter
from ornata.events.processing.propagation import EventPropagationEngine as EventPropagationEngine

__all__ = [
    "AsyncEventProcessor",
    "BatchedEventProcessor",
    "CliEventHandler",
    "EventBus",
    "EventDropFilter",
    "EventEntry",
    "EventFilter",
    "EventFilterManager",
    "EventFilterWrapper",
    "EventHandler",
    "EventHandlerManager",
    "EventHandlerWrapper",
    "EventModifyFilter",
    "EventObjectPool",
    "EventPool",
    "EventPoolConfig",
    "EventPoolStats",
    "EventPropagationEngine",
    "EventQueue",
    "EventReplayAnalyzer",
    "EventReplayBuffer",
    "EventReplayer",
    "EventSubsystem",
    "EventThrottleFilter",
    "EventTransformer",
    "GlobalEventBus",
    "LockFreeEventQueue",
    "PlatformEventHandler",
    "PooledComponentEvent",
    "PooledEvent",
    "PooledKeyEvent",
    "PooledMouseEvent",
    "SubsystemEventBus",
    "WindowsEventHandler",
    "add_event_listener",
    "async_processor",
    "bus",
    "create_cli_handler",
    "create_drop_filter",
    "create_event_replayer",
    "create_event_subsystem",
    "create_modify_filter",
    "create_platform_handler",
    "create_replay_analyzer",
    "create_replay_buffer",
    "create_throttle_filter",
    "create_windows_handler",
    "dispatch_cross_subsystem_event",
    "factory",
    "filtering",
    "get_event_object_pool",
    "handlers",
    "history",
    "pooled_component_event",
    "pooled_event",
    "pooled_key_event",
    "pooled_mouse_event",
    "processing",
    "propagation",
    "replay",
    "subsystem",
]
