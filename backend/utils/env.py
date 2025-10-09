import os
from typing import Literal

from dotenv import load_dotenv


def get_env(key: Literal["CORS_ORIGINS", "JWT_SECRET_KEY", "BACKEND_COOKIE_DOMAIN", "DEV"]) -> str:
    load_dotenv()
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Environment variable {key} is not set.")
    return value
