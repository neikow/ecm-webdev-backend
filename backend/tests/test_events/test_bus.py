import asyncio
from datetime import datetime

import pytest

from backend.domain.events import BaseEvent
from backend.events.bus import EventBus


def test_event_bus_should_be_initialized_with_empty_subscribers_and_a_lock():
    event_bus = EventBus()
    assert event_bus._subscribers == {}
    assert isinstance(event_bus._lock, asyncio.Lock)


@pytest.mark.asyncio
async def test_event_bus_should_put_event_on_subscriber_queue():
    event_bus = EventBus()
    queue = asyncio.Queue()
    untouched_queue = asyncio.Queue()
    event = BaseEvent(
        room_id=1,
        seq=0,
        ts=datetime.now(),
        type="event_type",
        data={},
    )
    event_bus._subscribers[event.room_id] = {queue}
    event_bus._subscribers[event.room_id + 1] = {untouched_queue}

    await event_bus.publish(event)

    assert queue.qsize() == 1
    assert untouched_queue.qsize() == 0


@pytest.mark.asyncio
async def test_event_bus_subscribe_to_room_events():
    room_id = 1
    event_bus = EventBus()

    async with event_bus.subscribe(room_id=room_id) as q:
        subs = event_bus._subscribers
        assert room_id in subs
        assert q in subs[room_id]


@pytest.mark.asyncio
async def test_event_bus_subscribe_cleanup():
    event_bus = EventBus()
    room_id = 1

    async with event_bus.subscribe(room_id) as q:
        subs = event_bus._subscribers
        assert room_id in subs
        assert q in subs[room_id]

    subs = event_bus._subscribers
    assert room_id not in subs or q not in subs.get(room_id, set())


@pytest.mark.asyncio
async def test_multiple_subscribers_and_room_key_cleanup():
    event_bus = EventBus()
    room_id = 42

    async with event_bus.subscribe(room_id) as q2:
        async with event_bus.subscribe(room_id) as q1:
            subs = event_bus._subscribers
            assert subs[room_id] == {q1, q2}

        subs = event_bus._subscribers
        assert room_id in subs and subs[room_id] == {q2}

        evt = BaseEvent(
            type="event",
            seq=1,
            ts=datetime.now(),
            room_id=room_id,
            data={}
        )

        await event_bus.publish(evt)
        assert await asyncio.wait_for(q2.get(), 0.2) is evt

    subs = event_bus._subscribers
    assert room_id not in subs
