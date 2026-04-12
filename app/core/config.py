from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "TU Pulse Backend"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5435
    POSTGRES_EXPOSE_PORT: int = 5435
    POSTGRES_DB: str = "tu_pulse"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"

    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    LINE_VERIFY_MODE: str = "mock"
    LINE_CHANNEL_ID: str | None = None
    LINE_CHANNEL_SECRET: str | None = None
    LINE_LIFF_ID: str | None = None

    AUTO_CREATE_TABLES: bool = True

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()