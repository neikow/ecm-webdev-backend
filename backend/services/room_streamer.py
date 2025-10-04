from fastapi import WebSocket

from backend.events.bus import EventBus
from backend.infra.memory_event_store import MemoryEventStore
from backend.infra.snapshots import SnapshotBuilderBase
from backend.routers.websocket_schemas import WSMessageSnapshot
from backend.utils.event import send_ws_message_event


class RoomStreamerService:
    @staticmethod
    async def restore_event_history(
            ws: WebSocket,
            room_id: int,
            last_seq: int | None,
            store: MemoryEventStore,
            snapshot_builder: SnapshotBuilderBase,
    ) -> None:
        history, current_last = await store.read_from(room_id)
        snapshot = await snapshot_builder.build(room_id, history)

        await ws.send_json(
            WSMessageSnapshot(
                type="snapshot",
                last_seq=current_last,
                data=snapshot,
            ).model_dump()
        )

        if last_seq is not None and last_seq < current_last:
            missed, _ = await store.read_from(room_id, after_seq=last_seq)
            for e in missed:
                await send_ws_message_event(e)

    @staticmethod
    async def stream_room_events(
            ws: WebSocket,
            room_id: int,
            event_bus: EventBus
    ) -> None:
        async with event_bus.subscribe(room_id) as queue:
            while True:
                e = await queue.get()
                await send_ws_message_event(e)
