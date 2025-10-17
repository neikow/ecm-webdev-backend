import asyncio
from typing import Generic, TypeVar

T = TypeVar("T")


class QueueSubscribers(Generic[T]):
    _subscribers_by_room_id: dict[int, set[asyncio.Queue[T]]]
    _subscribers_by_user_id: dict[str, asyncio.Queue[T]]

    def __init__(self):
        self._subscribers_by_user_id = {}
        self._subscribers_by_room_id = {}

    def add(self, room_id: int, user_id: str, q: asyncio.Queue[T]):
        self._subscribers_by_room_id.setdefault(room_id, set()).add(q)
        self._subscribers_by_user_id[user_id] = q

    def get_by_room_id(self, room_id: int) -> set[asyncio.Queue[T]]:
        return self._subscribers_by_room_id.get(room_id, set())

    def get_by_user_id(self, user_id: str) -> asyncio.Queue[T] | None:
        return self._subscribers_by_user_id.get(user_id)

    def remove(self, room_id: int, user_id: str, queue: asyncio.Queue[T]) -> None:
        self._subscribers_by_room_id[room_id].discard(queue)
        if not self._subscribers_by_room_id[room_id]:
            self._subscribers_by_room_id.pop(room_id, None)

        self._subscribers_by_user_id.pop(user_id, None)
