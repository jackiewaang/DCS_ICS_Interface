import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120
MAX_FAILED_LOGIN_ATTEMPTS = 10
LOGIN_RATE_LIMIT_ATTEMPTS = 10
LOGIN_RATE_LIMIT_WINDOW_SECONDS = 60


@dataclass(frozen=True)
class Settings:
    jwt_secret_key: str
    jwt_algorithm: str = JWT_ALGORITHM
    access_token_expire_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES
    max_failed_login_attempts: int = MAX_FAILED_LOGIN_ATTEMPTS
    login_rate_limit_attempts: int = LOGIN_RATE_LIMIT_ATTEMPTS
    login_rate_limit_window_seconds: int = LOGIN_RATE_LIMIT_WINDOW_SECONDS


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} environment variable must be set")
    return value


@lru_cache
def get_settings() -> Settings:
    load_dotenv(ENV_FILE)
    return Settings(
        jwt_secret_key=_required_env("JWT_SECRET_KEY"),
    )
