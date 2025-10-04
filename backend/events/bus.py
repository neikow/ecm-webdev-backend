import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from backend.domain.events import BaseEvent


class EventBus:
    _subscribers: dict[int, set[asyncio.Queue[BaseEvent]]]
    _lock: asyncio.Lock

    def __init__(self):
        self._subscribers = {}
        self._lock = asyncio.Lock()

    async def publish(self, event: BaseEvent) -> None:
        async with self._lock:
            for q in list(self._subscribers.get(event.room_id, ())):
                q.put_nowait(event)

    @asynccontextmanager
    async def subscribe(self, room_id: int) -> AsyncIterator[asyncio.Queue[BaseEvent]]:
        q: asyncio.Queue[BaseEvent] = asyncio.Queue()
        async with self._lock:
            self._subscribers.setdefault(room_id, set()).add(q)
        try:
            yield q
        finally:
            async with self._lock:
                self._subscribers[room_id].discard(q)
                if not self._subscribers[room_id]:
                    self._subscribers.pop(room_id, None)
