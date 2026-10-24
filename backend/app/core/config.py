from pathlib import Path

from pydantic import Field, PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    database_url: PostgresDsn
    organizer_token: SecretStr | None = Field(default=None, min_length=32)

    smtp_host: str = "127.0.0.1"
    smtp_port: int = Field(default=1025, ge=1, le=65535)
    smtp_from: str = "EventFlow <noreply@eventflow.local>"
    public_base_url: str = "http://localhost:5173"
    worker_interval: float = Field(default=1, ge=0.1, le=60)
    notification_lease_seconds: int = Field(default=120, ge=30, le=3600)

    @field_validator("organizer_token", mode="before")
    @classmethod
    def empty_token(cls, value: object) -> object:
        return None if value == "" else value
