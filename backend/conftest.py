import os
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from flexmock import flexmock
from sqlalchemy import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from backend.dependencies import get_event_bus, get_event_store
from backend.events.bus import EventBus
from backend.infra.memory_event_store import MemoryEventStore
from backend.infra.snapshots import SnapshotBuilderBase
from backend.server import app
from backend.utils.db import get_session


@pytest.fixture(name="session")
def db_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def mock_event_bus():
    return flexmock(EventBus())


@pytest.fixture()
def mock_event_store():
    return flexmock(MemoryEventStore())


@pytest.fixture()
def mock_snapshot_builder():
    return flexmock(SnapshotBuilderBase())


@pytest.fixture(name="client")
def client(session, mock_event_bus, mock_event_store):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_event_bus] = lambda: mock_event_bus
    app.dependency_overrides[get_event_store] = lambda: mock_event_store

    with TestClient(app) as c:
        yield c

    app.dependency_overrides = {}


@contextmanager
def mock_env(overrides: dict[str, str]):
    original = dict(os.environ)

    os.environ.update(overrides)
    try:
        yield os.environ
    finally:
        os.environ.clear()
        os.environ.update(original)


@pytest.fixture(name="mocked_env")
def mocked_env():
    yield mock_env


def test_mocked_env(mocked_env):
    with mocked_env({"test_var": "value"}):
        assert os.getenv("test_var") == "value"
