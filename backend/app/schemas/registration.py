from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegistrationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr = Field(max_length=254)

    @field_validator("email", mode="before")
    @classmethod
    def strip_email(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()


class RegistrationRead(BaseModel):
    id: UUID
    event_id: UUID
    email: str
    status: Literal["confirmed", "waiting", "cancelled"]
    queue_order: int
    queue_position: int | None
    created_at: datetime
    updated_at: datetime
    checked_in_at: datetime | None


class Availability(BaseModel):
    capacity: int
    confirmed: int
    waiting: int
    available: int
    registration_open: bool
    checked_in: int


class RegistrationPage(BaseModel):
    items: list[RegistrationRead]
    total: int
    limit: int
    offset: int
