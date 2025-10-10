from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from backend.routers.game_auth_router import router as game_auth_router
from backend.routers.game_room_router import router as game_room_router
from backend.routers.websocket import router as websocket_router
from backend.schemas.websocket.client import ClientMessageBase, ClientMessagePing, ClientMessageChatMessage
from backend.schemas.websocket.server import WSMessageBase, WSMessageSnapshot, WSMessageEvent, WSMessagePing, \
    WSMessageError, WSMessageResponse
from backend.utils.db import create_db_and_tables
from backend.utils.env import get_env
from backend.utils.errors import APIException

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    # allow_origins=get_env("CORS_ORIGINS").split(','),
    allow_origins=["https://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatMessageReceiveModel:
    user_name: str
    message: str


class ChatMessageSendModel:
    message: str


@app.exception_handler(APIException)
def api_error_handler(_, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )


app.include_router(game_room_router)
app.include_router(websocket_router)
app.include_router(game_auth_router)

if get_env("DEV") == "true":
    types_router = APIRouter(prefix="/types")


    @types_router.get(
        "/ws/server",
        response_model=WSMessageBase
                       | WSMessageSnapshot
                       | WSMessageEvent
                       | WSMessagePing
                       | WSMessageError
                       | WSMessageResponse
                       | None
    )
    async def get_types_server():
        return None


    @types_router.get(
        "/ws/client",
        response_model=ClientMessageBase
                       | ClientMessagePing
                       | ClientMessageChatMessage
                       | None
    )
    async def get_types_client():
        return None


    app.include_router(types_router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
