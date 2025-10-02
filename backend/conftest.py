import os
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool
from sqlmodel import Session, SQLModel, create_engine

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


@pytest.fixture(name="client")
def client(session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

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
