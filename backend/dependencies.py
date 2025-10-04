from backend.events.bus import EventBus
from backend.infra.memory_event_store import MemoryEventStore
from backend.infra.snapshots import SnapshotBuilderBase
from backend.state.connection_manager import ConnectionManager

_connections = ConnectionManager()
_store = MemoryEventStore()
_snapshot_builder = SnapshotBuilderBase()
_event_bus = EventBus()


def get_connection_manager() -> ConnectionManager:
    return _connections


def get_event_store() -> MemoryEventStore:
    return _store


def get_snapshot_builder() -> SnapshotBuilderBase:
    return _snapshot_builder


def get_event_bus() -> EventBus:
    return _event_bus
