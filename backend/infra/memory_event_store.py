import asyncio
from collections import defaultdict
from logging import getLogger

from backend.domain.events import BaseEvent

logger = getLogger(__name__)


class MemoryEventStore:
    _events: dict[int, list[BaseEvent]]
    _locks: dict[int, asyncio.Lock]

    def __init__(self):
        logger.info("Initializing MemoryEventStore")

        self._events = defaultdict(list)
        self._locks = defaultdict(asyncio.Lock)

    async def append(
            self,
            room_id: int,
            event_type: str,
            data: dict | None = None,
            actor_id: str | None = None
    ) -> BaseEvent:
        lock = self._locks[room_id]
        async with lock:
            seq = len(self._events[room_id]) + 1
            event = BaseEvent(
                seq=seq,
                room_id=room_id,
                type=event_type,
                actor_id=actor_id,
                data=data or {}
            )
            logger.info(f"Appending event: {event.model_dump()}")
            self._events[room_id].append(event)
            return event

    async def read_from(
            self,
            room_id:
            int,
            after_seq: int | None = None,
            limit: int = 500
    ) -> tuple[
        list[BaseEvent], int
    ]:
        logger.info(f"Reading events for room_id={room_id}")
        events = self._events.get(room_id, [])
        if after_seq is None:
            slice_ = events[-limit:]
        else:
            slice_ = [e for e in events if e.seq > after_seq][:limit]
        last_seq = events[-1].seq if events else 0
        return slice_, last_seq

    async def last_seq(self, room_id: int) -> int:
        events = self._events.get(room_id, [])
        return events[-1].seq if events else 0
