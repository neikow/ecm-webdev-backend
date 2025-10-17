import asyncio

from backend.events.subscribers import QueueSubscribers


def test_subscribers_should_initialize_empty_dicts():
    subscribers = QueueSubscribers[int]()
    assert subscribers._subscribers_by_room_id == {}
    assert subscribers._subscribers_by_user_id == {}


def test_subscribers_should_add_subscribers_to_store():
    subscribers = QueueSubscribers[int]()
    queue = asyncio.Queue()
    subscribers.add(
        1,
        "user",
        queue,
    )
    assert subscribers._subscribers_by_room_id.get(1) == {queue}
    assert subscribers._subscribers_by_user_id.get('user') == queue


def test_subscribers_get_by_room_id_should_return_a_set_of_queues():
    subscribers = QueueSubscribers[int]()
    queue = asyncio.Queue()
    subscribers.add(
        1,
        "user",
        queue,
    )
    assert subscribers.get_by_room_id(1) == {queue}


def test_subscribers_get_by_room_id_should_raise_key_error_if_the_room_id_does_not_exist():
    subscribers = QueueSubscribers[int]()
    assert subscribers.get_by_room_id(0) == set()


def test_subscribers_get_by_user_id_should_return_a_queue():
    subscibers = QueueSubscribers[int]()
    queue = asyncio.Queue()
    subscibers.add(
        1,
        "user",
        queue
    )
    assert subscibers.get_by_user_id("user")


def test_subscribers_get_by_user_id_should_raise_key_error_if_the_user_id_does_not_exist():
    subscribers = QueueSubscribers[int]()
    assert subscribers.get_by_user_id("0") is None


def test_remove_subscriber():
    subscribers = QueueSubscribers[int]()
    queue1 = asyncio.Queue()
    queue2 = asyncio.Queue()
    room_id = 0
    subscribers.add(
        room_id,
        "user1",
        queue1
    )
    subscribers.add(
        room_id,
        "user2",
        queue2
    )
    assert len(subscribers._subscribers_by_user_id) == 2
    assert len(subscribers._subscribers_by_room_id) == 1

    subscribers.remove(room_id, "user1", queue1)

    assert len(subscribers._subscribers_by_user_id) == 1
    assert len(subscribers._subscribers_by_room_id) == 1

    subscribers.remove(room_id, "user2", queue2)

    assert len(subscribers._subscribers_by_user_id) == 0
    assert len(subscribers._subscribers_by_room_id) == 0
