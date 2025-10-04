import pytest
from flexmock import flexmock

from backend.domain.events import BaseEvent
from backend.utils.event import send_ws_message_event
from backend.utils.future import build_future


@pytest.mark.asyncio
async def test_send_ws_message_event() -> None:
    event = BaseEvent(
        room_id=1,
        data={"key": "value"},
        seq=1,
        type="test_event"
    )
    ws = flexmock()
    ws.should_receive("send_json").once().with_args(
        {
            "type": "event",
            "seq": event.seq,
            "event": event.model_dump(),
        }
    ).and_return(build_future(None))
    await send_ws_message_event(
        ws,  # type: ignore[arg-type]
        event
    )
