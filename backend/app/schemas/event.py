from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=10000)]
Capacity = Annotated[int, Field(strict=True, gt=0, le=1000000)]


class EventInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("starts_at", check_fields=False)
    @classmethod
    def validate_start(cls, value: datetime) -> datetime:
        if value <= datetime.now(UTC):
            raise ValueError("Дата мероприятия должна быть в будущем")
        return value.astimezone(UTC)


class EventCreate(EventInput):
    title: Title
    description: Description = ""
    starts_at: AwareDatetime
    capacity: Capacity


class EventUpdate(EventInput):
    title: Title | None = None
    description: Description | None = None
    starts_at: AwareDatetime | None = None
    capacity: Capacity | None = None

    @field_validator("*", mode="before")
    @classmethod
    def reject_null(cls, value: object) -> object:
        if value is None:
            raise ValueError("Поле не может быть null")
        return value

    @model_validator(mode="after")
    def reject_empty(self) -> "EventUpdate":
        if not self.model_fields_set:
            raise ValueError("Укажите хотя бы одно поле")
        return self


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    starts_at: AwareDatetime
    capacity: int
    confirmed_count: int
    schedule_version: int
    created_at: AwareDatetime
    updated_at: AwareDatetime


class EventPage(BaseModel):
    items: list[EventRead]
    total: int
    limit: int
    offset: int
