from typing import Literal

from pydantic import BaseModel

from backend.domain.events import BaseEvent
from backend.infra.snapshots import SnapshotBase


class WSMessageSnapshot(BaseModel):
    type: Literal["snapshot"] = "snapshot"
    last_seq: int
    data: SnapshotBase


class WSMessageEvent(BaseModel):
    type: Literal["event"] = "event"
    seq: int
    event: BaseEvent
