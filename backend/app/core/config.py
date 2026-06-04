from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file() -> str:
    for candidate in [Path(".env"), Path("../.env")]:
        if candidate.exists():
            return str(candidate)
    return ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_find_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # PostgreSQL
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # Redis
    REDIS_URL: str

    # MinIO
    MINIO_ENDPOINT: str
    MINIO_PUBLIC_ENDPOINT: str = ""
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str
    MINIO_USE_SSL: bool = False

    # Telegram
    TELEGRAM_BOT_TOKEN: str

    # First admin bootstrap
    FIRST_ADMIN_PHONE: str = "+77000000000"
    FIRST_ADMIN_NAME: str = "Admin"
    FIRST_ADMIN_PASSWORD: str = "change_me_in_production"

    # App
    APP_ENV: str = "development"
    SECRET_KEY: str
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
