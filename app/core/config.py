from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # =========================
    # App Info
    # =========================
    APP_NAME: str = "Demand Planning Agent"
    APP_VERSION: str = "1.0.0"

    # =========================
    # PostgreSQL
    # =========================
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # =========================
    # FalkorDB
    # =========================
    FALKOR_HOST: str
    FALKOR_PORT: int
    FALKOR_GRAPH: str

    # =========================
    # Postal (OLD - keep it)
    # =========================
    POSTAL_BASE_URL: str
    POSTAL_SERVER_KEY: str
    POSTAL_FROM_EMAIL: str
    POSTAL_WEBHOOK_URL: str

    # =========================
    # Postal SMTP (NEW - ADD THIS)
    # =========================
    POSTAL_SMTP_HOST: str
    POSTAL_SMTP_PORT: int
    POSTAL_SMTP_USER: str
    POSTAL_SMTP_PASS: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()