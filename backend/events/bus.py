import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from backend.domain.events import BaseEvent
from backend.events.subscribers import QueueSubscribers


class EventBus:
    _subscribers: QueueSubscribers[BaseEvent]
    _lock: asyncio.Lock

    def __init__(self):
        self._subscribers = QueueSubscribers[BaseEvent]()
        self._lock = asyncio.Lock()

    async def publish(self, event: BaseEvent) -> None:
        async with self._lock:
            if event.target_id:
                q = self._subscribers.get_by_user_id(event.target_id)
                if q is None:
                    raise ValueError
                q.put_nowait(event)
            else:
                for q in list(self._subscribers.get_by_room_id(event.room_id)):
                    q.put_nowait(event)

    @asynccontextmanager
    async def subscribe(self, room_id: int, user_id: str) -> AsyncIterator[asyncio.Queue[BaseEvent]]:
        q: asyncio.Queue[BaseEvent] = asyncio.Queue()
        async with self._lock:
            self._subscribers.add(room_id, user_id, q)
        try:
            yield q
        finally:
            async with self._lock:
                self._subscribers.remove(room_id, user_id, q)
