from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.game_room_router import router as game_room_router
from backend.routers.websocket import router as websocket_router
from backend.utils.db import create_db_and_tables
from backend.utils.env import get_env

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_env("CORS_ORIGINS").split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessageReceiveModel:
    user_name: str
    message: str


class ChatMessageSendModel:
    message: str


app.include_router(game_room_router)
app.include_router(websocket_router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
