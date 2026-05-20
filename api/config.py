from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = "development"
    app_name: str = "under-over"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/under_over"

    model_config = SettingsConfigDict(
        env_prefix="UNDER_OVER_",
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
