import asyncio
from asyncio import Future
from typing import TypeVar

T = TypeVar("T")


async def build_future(value: T) -> Future[T]:
    return await asyncio.sleep(0, result=value)
