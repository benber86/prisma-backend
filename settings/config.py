import os
from pathlib import Path

import dotenv
from pydantic import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    DEBUG: bool = True
    DEV: bool = True
    APP_URI_PREFIX: str | None = None

    ALCHEMY_API_KEY: str | None = None
    WEB3_REQUEST_TIMEOUT: int | None = 30
    # PostgreSQL credentials
    PG_HOST: str
    PG_PORT: int
    PG_USER: str
    PG_PASSWORD: str
    PG_DATABASE: str

    ETHERSCAN_TOKEN: str | None
    REDIS_PASSWORD: str

    CELERY_BROKER_URL: str | None
    CELERY_RESULT_BACKEND: str | None
    CACHE_REDIS_URL: str | None

    def pg_conn_str(self):
        return f"postgresql://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DATABASE}"

    class Config:
        os.environ["FASTAPI_TITLE"] = "Prisma backend"
        env_file = Path(BASE_DIR, ".env")
        dotenv.load_dotenv(env_file)


settings = Settings()
