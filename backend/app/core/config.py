from pathlib import Path

from pydantic import Field, PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    database_url: PostgresDsn
    organizer_token: SecretStr | None = Field(default=None, min_length=32)

    @field_validator("organizer_token", mode="before")
    @classmethod
    def empty_token(cls, value: object) -> object:
        return None if value == "" else value
