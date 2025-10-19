import pytest

from backend.infra.memory_event_store import MemoryEventStore


def test_memory_event_store_should_initialize():
    event_store = MemoryEventStore()
    assert event_store._events == {}
    assert event_store._locks == {}


@pytest.mark.asyncio
async def test_append_to_memory_event_store_returning_the_event():
    event_store = MemoryEventStore()
    room_id = 1

    event = await event_store.append(
        room_id=room_id,
        event_type="event",
    )

    assert len(event_store._events[room_id]) == 1
    assert event_store._events[room_id] == [
        event
    ]


@pytest.mark.asyncio
async def test_read_from_memory_event_store():
    event_store = MemoryEventStore()
    room_id = 1

    event = await event_store.append(room_id, "event")
    result = await event_store.read_from(room_id=room_id)

    assert result == ([event], 1)


@pytest.mark.asyncio
async def test_read_from_memory_event_store_starting_at_seq():
    event_store = MemoryEventStore()
    room_id = 1

    await event_store.append(room_id, "event")
    event = await event_store.append(room_id, "event")

    result = await event_store.read_from(room_id=room_id, after_seq=1)
    assert result == (
        [event], 2
    )


@pytest.mark.asyncio
async def test_read_from_memory_event_store_with_limit():
    event_store = MemoryEventStore()
    room_id = 1

    await event_store.append(room_id, "event")
    event2 = await event_store.append(room_id, "event")

    result = await event_store.read_from(
        room_id=room_id, limit=1,
    )

    assert result == (
        [event2], 2
    )


@pytest.mark.asyncio
async def test_read_from_memory_event_store_with_limit_and_after_seq():
    event_store = MemoryEventStore()
    room_id = 1

    await event_store.append(room_id, "event")
    event = await event_store.append(room_id, "event")
    await event_store.append(room_id, "event")

    result = await event_store.read_from(
        room_id=room_id, limit=1, after_seq=1,
    )

    assert result == (
        [event], 3
    )


@pytest.mark.asyncio
async def test_get_last_seq_for_memory_event_store():
    event_store = MemoryEventStore()
    room_id = 1

    assert await event_store.last_seq(room_id) == 0

    await event_store.append(room_id, "event")
    assert await event_store.last_seq(room_id) == 1

    await event_store.append(room_id, "event")
    assert await event_store.last_seq(room_id) == 2


@pytest.mark.asyncio
async def test_append_event_with_target_id():
    event_store = MemoryEventStore()
    room_id = 1

    event = await event_store.append(
        room_id=room_id,
        event_type="event",
        target_id="target_user"
    )

    assert event.target_id == "target_user"
    assert len(event_store._events[room_id]) == 1
    assert event_store._events[room_id] == [
        event
    ]
