import asyncio
from datetime import datetime

import pytest

from backend.domain.events import BaseEvent
from backend.events.bus import EventBus
from backend.events.subscribers import QueueSubscribers


def test_event_bus_should_be_initialized_with_empty_subscribers_and_a_lock():
    event_bus = EventBus()
    assert isinstance(event_bus._subscribers, QueueSubscribers)
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
    event_bus._subscribers.add(event.room_id, "user1", queue)
    event_bus._subscribers.add(event.room_id + 1, "user2", untouched_queue)

    await event_bus.publish(event)

    assert queue.qsize() == 1
    assert untouched_queue.qsize() == 0


@pytest.mark.asyncio
async def test_event_bus_subscribe_to_room_events():
    room_id = 1
    event_bus = EventBus()

    async with event_bus.subscribe(room_id=room_id, user_id="user") as q:
        subs = event_bus._subscribers
        assert q in subs.get_by_room_id(room_id)
        assert q == subs.get_by_user_id("user")


@pytest.mark.asyncio
async def test_event_bus_subscribe_cleanup():
    event_bus = EventBus()
    room_id = 1

    async with event_bus.subscribe(room_id, 'user') as q:
        subs = event_bus._subscribers
        assert q in subs.get_by_room_id(room_id)
        assert q == subs.get_by_user_id('user')

    subs = event_bus._subscribers
    assert room_id not in subs._subscribers_by_room_id or q not in subs.get_by_room_id(room_id)


@pytest.mark.asyncio
async def test_multiple_subscribers_and_room_key_cleanup():
    event_bus = EventBus()
    room_id = 42

    async with event_bus.subscribe(room_id, 'user2') as q2:
        async with event_bus.subscribe(room_id, 'user1') as q1:
            subs = event_bus._subscribers
            assert subs.get_by_room_id(room_id) == {q1, q2}

        subs = event_bus._subscribers
        assert room_id in subs._subscribers_by_room_id and subs.get_by_room_id(room_id) == {q2}

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
    assert room_id not in subs._subscribers_by_room_id


@pytest.mark.asyncio
async def test_bus_publish_to_a_single_target():
    event_bus = EventBus()
    room_id = 42
    user1 = "user1"
    user2 = "user2"

    async with event_bus.subscribe(room_id, user2) as q2:
        async with event_bus.subscribe(room_id, user1) as q1:
            await event_bus.publish(
                BaseEvent(
                    room_id=room_id,
                    type="event",
                    seq=1,
                    data={},
                    target_id=user1
                )
            )

            assert q1.qsize() == 1
            assert q2.qsize() == 0


@pytest.mark.asyncio
async def test_bus_publish_to_a_single_non_existant_target():
    event_bus = EventBus()
    with pytest.raises(ValueError):
        await event_bus.publish(
            BaseEvent(
                room_id=0,
                type="event",
                seq=1,
                data={},
                target_id="-unknown-user"
            )
        )
