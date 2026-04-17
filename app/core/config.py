from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # =========================
    # App Info (KEEP THIS)
    # =========================
    APP_NAME: str = "Demand Planning Agent"
    APP_VERSION: str = "1.0.0"

    # =========================
    # PostgreSQL Config
    # =========================
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # =========================
    # FalkorDB Config
    # =========================
    FALKOR_HOST: str
    FALKOR_PORT: int
    FALKOR_GRAPH: str

    # =========================
    # Postal Config (NEW)
    # =========================
    POSTAL_BASE_URL: str
    POSTAL_SERVER_KEY: str
    POSTAL_FROM_EMAIL: str
    POSTAL_WEBHOOK_URL: str

    # =========================
    # Database URL Builder
    # =========================
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton instance
@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()