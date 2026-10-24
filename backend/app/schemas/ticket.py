from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    registration_id: UUID
    code: str
    created_at: datetime
    checked_in_at: datetime | None


class TicketCode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(pattern=r"^[0-9A-F]{32}$")]

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: object) -> object:
        if isinstance(value, str):
            if len(value) > 256:
                raise ValueError("Слишком длинный код билета")
            return value.strip().replace("-", "").replace(" ", "").upper()
        return value


class TicketVerification(TicketRead):
    event_id: UUID
    email: str
    status: Literal["valid", "checked_in", "revoked"]
    revoked_at: datetime | None


class CheckInResult(BaseModel):
    ticket: TicketVerification
    already_checked_in: bool
