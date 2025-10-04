from unittest.mock import MagicMock

import pytest

from backend.state.connection_manager import ConnectionManager


def test_connection_manager_should_be_initialized_with_empty_connections_dict():
    assert ConnectionManager().rooms == {}


@pytest.mark.asyncio
async def test_add_websocket_to_connection_manager():
    manager = ConnectionManager()
    ws = MagicMock()
    room_id = 1
    await manager.connect(room_id=room_id, ws=ws)
    assert ws in manager.rooms[room_id]


@pytest.mark.asyncio
async def test_remove_websocket_from_connection_manager():
    manager = ConnectionManager()
    ws1 = MagicMock()
    ws2 = MagicMock()
    room_id = 1
    manager.rooms[room_id] = {ws1, ws2}
    await manager.disconnect(room_id=room_id, ws=ws1)
    assert ws1 not in manager.rooms[room_id]


@pytest.mark.asyncio
async def test_remove_last_websocket_removes_the_room_from_connection_manager():
    manager = ConnectionManager()
    ws = MagicMock()
    room_id = 1
    manager.rooms[room_id] = {ws}
    await manager.disconnect(room_id=room_id, ws=ws)
    assert room_id not in manager.rooms
