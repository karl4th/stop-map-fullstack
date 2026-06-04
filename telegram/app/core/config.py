from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file() -> str:
    for candidate in [Path(".env"), Path("../.env"), Path("../../.env")]:
        if candidate.exists():
            return str(candidate)
    return ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_find_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    TELEGRAM_BOT_TOKEN: str
    REDIS_URL: str = "redis://localhost:6379/0"
    BACKEND_URL: str = "http://localhost:8000/api"


settings = Settings()
