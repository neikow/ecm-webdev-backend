from fastapi import FastAPI

from backend.server import app


def test_app_init():
    assert app is not None
    assert isinstance(app, FastAPI)
