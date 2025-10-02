from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.routers.game_room_router import router as game_room_router
from backend.utils.db import create_db_and_tables

app = FastAPI()
app.include_router(game_room_router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
