import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Monitoring Innovation API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./monitoring_innovation.db"

    # JWT — si no se configura via .env, se genera una clave aleatoria cada vez que arranca el servidor
    SECRET_KEY: str = secrets.token_urlsafe(64)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    # SMTP / Email Configuration (opcional — fallback a consola si no se configura)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "juanchotv123@gmail.com"
    SMTP_PASSWORD: str = "txqooiytpsilxuun"
    SMTP_FROM_EMAIL: str = "juanchotv123@gmail.com"
    SMTP_FROM_NAME: str = "Monitoring Innovation"
    FRONTEND_URL: str = "http://localhost:5173"
    PASSWORD_HISTORY_LIMIT: int = 5


settings = Settings()
