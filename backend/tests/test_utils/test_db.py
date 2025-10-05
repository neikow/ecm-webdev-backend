from flexmock import flexmock
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from sqlmodel import SQLModel

from backend.utils.db import create_db_and_tables, get_session


def test_create_db_and_tables():
    flexmock(SQLModel.metadata).should_receive(
        "create_all"
    ).with_args(
        Engine
    ).once()
    create_db_and_tables()


def test_get_session_generator():
    gen = get_session()

    session = next(gen)
    assert session is not None
    assert isinstance(session, Session)
