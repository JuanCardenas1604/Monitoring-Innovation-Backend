import secrets
from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Monitoring Innovation API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database — SQLite en local; Railway inyecta PostgreSQL vía DATABASE_URL
    DATABASE_URL: str = "sqlite:///./monitoring_innovation.db"

    # JWT (obligatorio en producción: definir SECRET_KEY en Railway)
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS — en Railway: valor plano (https://x.com o varias separadas por coma)
    CORS_ORIGINS: str = "*"

    # SMTP (opcional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "Monitoring Innovation"
    FRONTEND_URL: str = "http://localhost:5173"
    PASSWORD_HISTORY_LIMIT: int = 5

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        if value.startswith("postgres://"):
            value = value.replace("postgres://", "postgresql+psycopg://", 1)
        elif value.startswith("postgresql://") and "+" not in value.split("://", 1)[0]:
            value = value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> str:
        if value is None or value == "":
            return "*"
        return str(value)

    @model_validator(mode="after")
    def ensure_secret_key(self) -> "Settings":
        if not self.SECRET_KEY:
            if not self.DEBUG:
                raise ValueError(
                    "SECRET_KEY es obligatorio en producción. "
                    "Configúralo en Railway → Variables."
                )
            object.__setattr__(self, "SECRET_KEY", secrets.token_urlsafe(64))
        return self

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def smtp_configured(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_USERNAME and self.SMTP_PASSWORD)

    @property
    def cors_origins_list(self) -> list[str]:
        value = self.CORS_ORIGINS.strip()
        if value == "*":
            return ["*"]
        return [origin.strip() for origin in value.split(",") if origin.strip()]


settings = Settings()
