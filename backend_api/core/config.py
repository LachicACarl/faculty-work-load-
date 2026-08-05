from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Faculty Workload Allocation API"
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/faculty_workload"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
