from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://agreements:agreements@localhost:5432/agreements"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"


settings = Settings()
