from asyncio import Future
from typing import TypeVar

T = TypeVar("T")


def build_future(value: T) -> Future[T]:
    future: Future[T] = Future()
    future.set_result(value)
    return future
